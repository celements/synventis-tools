#!/usr/bin/env python3
"""Fetch a complete, read-only GitHub pull-request context as JSON."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, TypeVar
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0"
PAGE_SIZE = 100
MAX_PAGES = 10_000


class RetrievalError(RuntimeError):
    """Raised when a complete, internally consistent snapshot cannot be produced."""


@dataclass(frozen=True)
class PullRequestTarget:
    hostname: str
    owner: str
    repository: str
    number: int

    @property
    def name_with_owner(self) -> str:
        return f"{self.owner}/{self.repository}"

    @classmethod
    def parse(cls, value: str, default_hostname: str = "github.com") -> PullRequestTarget:
        candidate = value.strip()
        if "://" in candidate:
            parsed = urlparse(candidate)
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) < 4 or parts[2] != "pull" or not parts[3].isdigit():
                raise RetrievalError(
                    "Expected a GitHub pull-request URL such as "
                    "https://github.com/OWNER/REPOSITORY/pull/NUMBER"
                )
            return cls(
                hostname=parsed.hostname or default_hostname,
                owner=parts[0],
                repository=parts[1].removesuffix(".git"),
                number=int(parts[3]),
            )
        match = re.fullmatch(
            r"(?P<owner>[^/\s#]+)/(?P<repository>[^#\s]+)#(?P<number>[1-9]\d*)",
            candidate,
        )
        if not match:
            raise RetrievalError(
                "Expected OWNER/REPOSITORY#NUMBER or a GitHub pull-request URL"
            )
        return cls(
            hostname=default_hostname,
            owner=match.group("owner"),
            repository=match.group("repository").removesuffix(".git"),
            number=int(match.group("number")),
        )


def _redact_error(value: str) -> str:
    redacted = re.sub(
        r"(?i)(authorization\s*:\s*bearer|token\s*[=:])\s*\S+",
        r"\1 [redacted]",
        value.strip(),
    )
    return redacted[:2_000]


class GhClient:
    """Minimal authenticated GitHub API client backed by the gh CLI."""

    def __init__(self, hostname: str, attempts: int = 2) -> None:
        self.hostname = hostname
        self.attempts = attempts

    def rest(self, endpoint: str, fields: dict[str, int] | None = None) -> Any:
        command = [
            "gh",
            "api",
            endpoint,
            "--hostname",
            self.hostname,
            "--method",
            "GET",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
        ]
        for key, value in (fields or {}).items():
            command.extend(["-F", f"{key}={value}"])
        return self._run_json(command)

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables})
        response = self._run_json(
            [
                "gh",
                "api",
                "graphql",
                "--hostname",
                self.hostname,
                "--input",
                "-",
            ],
            payload,
        )
        if not isinstance(response, dict):
            raise RetrievalError("GitHub GraphQL returned a non-object response")
        errors = response.get("errors")
        if errors:
            messages = [
                str(error.get("message", "unknown GraphQL error"))
                for error in errors
                if isinstance(error, dict)
            ]
            raise RetrievalError("GitHub GraphQL error: " + "; ".join(messages))
        return response

    def _run_json(self, command: list[str], input_text: str | None = None) -> Any:
        failure = "unknown gh failure"
        for attempt in range(self.attempts):
            try:
                result = subprocess.run(
                    command,
                    input=input_text,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            except FileNotFoundError as error:
                raise RetrievalError("The authenticated gh CLI is required") from error
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as error:
                    raise RetrievalError("GitHub API returned invalid JSON") from error
            failure = _redact_error(result.stderr or result.stdout)
            if attempt + 1 < self.attempts:
                time.sleep(0.25)
        raise RetrievalError(f"gh API request failed: {failure}")


CORE_QUERY = """
query FetchPullRequestCore($owner: String!, $repository: String!, $number: Int!) {
  viewer {
    login
    url
  }
  repository(owner: $owner, name: $repository) {
    nameWithOwner
    url
    pullRequest(number: $number) {
      id
      number
      url
      title
      body
      state
      isDraft
      merged
      mergedAt
      closed
      closedAt
      createdAt
      updatedAt
      publishedAt
      author {
        login
        url
      }
      authorAssociation
      baseRefName
      baseRefOid
      baseRepository {
        nameWithOwner
        url
      }
      headRefName
      headRefOid
      headRepository {
        nameWithOwner
        url
      }
      isCrossRepository
      maintainerCanModify
      mergeable
      mergeStateStatus
      reviewDecision
      viewerDidAuthor
      viewerLatestReview {
        id
        fullDatabaseId
        state
        submittedAt
        commit {
          oid
        }
      }
      viewerLatestReviewRequest {
        id
        asCodeOwner
        requestedReviewer {
          __typename
          ... on User {
            login
            name
            url
          }
          ... on Team {
            slug
            name
            url
            organization {
              login
            }
          }
        }
      }
      statusCheckRollup {
        state
        contexts(first: 1) {
          totalCount
        }
      }
      assignees(first: 1) { totalCount }
      labels(first: 1) { totalCount }
      reviewRequests(first: 1) { totalCount }
      comments(first: 1) { totalCount }
      reviews(first: 1) { totalCount }
      commits(first: 1) { totalCount }
      files(first: 1) { totalCount }
      reviewThreads(first: 1) { totalCount }
    }
  }
  rateLimit {
    cost
    remaining
    resetAt
  }
}
"""

ASSIGNEES_QUERY = """
query FetchAssignees($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      assignees(first: 100, after: $cursor) {
        totalCount
        nodes { id login name url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

LABELS_QUERY = """
query FetchLabels($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      labels(first: 100, after: $cursor) {
        totalCount
        nodes { id name color description }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

REVIEW_REQUESTS_QUERY = """
query FetchReviewRequests($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      reviewRequests(first: 100, after: $cursor) {
        totalCount
        nodes {
          id
          asCodeOwner
          requestedReviewer {
            __typename
            ... on User { login name url }
            ... on Team { slug name url organization { login } }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

COMMENTS_QUERY = """
query FetchPullRequestComments($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      comments(first: 100, after: $cursor) {
        totalCount
        nodes {
          id
          fullDatabaseId
          author { login url }
          authorAssociation
          body
          createdAt
          updatedAt
          url
          isMinimized
          minimizedReason
          viewerDidAuthor
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

REVIEWS_QUERY = """
query FetchPullRequestReviews($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      reviews(first: 100, after: $cursor) {
        totalCount
        nodes {
          id
          fullDatabaseId
          author { login url }
          authorAssociation
          body
          state
          submittedAt
          createdAt
          updatedAt
          url
          viewerDidAuthor
          commit { oid }
          comments { totalCount }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

THREAD_COMMENT_FIELDS = """
id
fullDatabaseId
author { login url }
authorAssociation
body
state
createdAt
updatedAt
publishedAt
url
path
line
startLine
originalLine
originalStartLine
outdated
diffHunk
viewerDidAuthor
replyTo { id fullDatabaseId }
pullRequestReview {
  id
  fullDatabaseId
  state
  submittedAt
  author { login url }
  commit { oid }
}
"""

REVIEW_THREADS_QUERY = f"""
query FetchReviewThreads($id: ID!, $cursor: String) {{
  node(id: $id) {{
    ... on PullRequest {{
      reviewThreads(first: 100, after: $cursor) {{
        totalCount
        nodes {{
          id
          isCollapsed
          isOutdated
          isResolved
          path
          line
          startLine
          originalLine
          originalStartLine
          diffSide
          startDiffSide
          subjectType
          viewerCanReply
          viewerCanResolve
          viewerCanUnresolve
          resolvedBy {{ login url }}
          comments(first: 100) {{
            totalCount
            nodes {{ {THREAD_COMMENT_FIELDS} }}
            pageInfo {{ hasNextPage endCursor }}
          }}
        }}
        pageInfo {{ hasNextPage endCursor }}
      }}
    }}
  }}
}}
"""

THREAD_COMMENTS_QUERY = f"""
query FetchReviewThreadComments($id: ID!, $cursor: String) {{
  node(id: $id) {{
    ... on PullRequestReviewThread {{
      id
      comments(first: 100, after: $cursor) {{
        totalCount
        nodes {{ {THREAD_COMMENT_FIELDS} }}
        pageInfo {{ hasNextPage endCursor }}
      }}
    }}
  }}
}}
"""

THREAD_STATES_QUERY = """
query FetchReviewThreadStates($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on PullRequest {
      reviewThreads(first: 100, after: $cursor) {
        totalCount
        nodes {
          id
          isCollapsed
          isOutdated
          isResolved
          path
          line
          startLine
          comments(last: 1) {
            totalCount
            nodes { id state updatedAt }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

T = TypeVar("T")


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RetrievalError(f"GitHub response is missing object: {label}")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RetrievalError(f"GitHub response is missing list: {label}")
    return value


def _connection_from_node(response: dict[str, Any], name: str) -> dict[str, Any]:
    data = _require_dict(response.get("data"), "data")
    node = _require_dict(data.get("node"), "data.node")
    return _require_dict(node.get(name), f"data.node.{name}")


def _page_info(connection: dict[str, Any], label: str) -> tuple[bool, str | None]:
    page_info = _require_dict(connection.get("pageInfo"), f"{label}.pageInfo")
    has_next = page_info.get("hasNextPage")
    if not isinstance(has_next, bool):
        raise RetrievalError(f"GitHub response has invalid hasNextPage for {label}")
    cursor = page_info.get("endCursor")
    if has_next and not isinstance(cursor, str):
        raise RetrievalError(f"GitHub response has no endCursor for incomplete {label}")
    return has_next, cursor


def _paginate_graphql_connection(
    client: GhClient,
    query: str,
    pull_request_id: str,
    name: str,
    expected_count: int,
    normalize: Callable[[dict[str, Any]], T],
) -> tuple[list[T], dict[str, int]]:
    items: list[T] = []
    cursor: str | None = None
    pages = 0
    seen_ids: set[str] = set()
    while True:
        if pages >= MAX_PAGES:
            raise RetrievalError(f"Exceeded pagination limit for {name}")
        response = client.graphql(query, {"id": pull_request_id, "cursor": cursor})
        connection = _connection_from_node(response, name)
        total_count = connection.get("totalCount")
        if total_count != expected_count:
            raise RetrievalError(
                f"{name} changed or is incomplete: expected {expected_count}, got {total_count}"
            )
        nodes = _require_list(connection.get("nodes"), f"{name}.nodes")
        for raw_node in nodes:
            node = _require_dict(raw_node, f"{name}.node")
            node_id = node.get("id")
            if isinstance(node_id, str):
                if node_id in seen_ids:
                    raise RetrievalError(f"Duplicate node while paginating {name}: {node_id}")
                seen_ids.add(node_id)
            items.append(normalize(node))
        pages += 1
        has_next, cursor = _page_info(connection, name)
        if not has_next:
            break
    if len(items) != expected_count:
        raise RetrievalError(
            f"{name} item count is incomplete: expected {expected_count}, got {len(items)}"
        )
    return items, {"expected_items": expected_count, "retrieved_items": len(items), "pages": pages}


def _paginate_rest_list(
    client: GhClient,
    endpoint: str,
    name: str,
    expected_count: int,
    normalize: Callable[[dict[str, Any]], T],
) -> tuple[list[T], dict[str, int]]:
    items: list[T] = []
    page = 1
    seen_items: set[tuple[str, str]] = set()
    while True:
        if page > MAX_PAGES:
            raise RetrievalError(f"Exceeded pagination limit for {name}")
        response = client.rest(endpoint, {"per_page": PAGE_SIZE, "page": page})
        nodes = _require_list(response, name)
        for raw_node in nodes:
            node = _require_dict(raw_node, f"{name}.item")
            identity = _rest_item_identity(node, name)
            if identity in seen_items:
                raise RetrievalError(f"Duplicate item while paginating {name}: {identity[1]}")
            seen_items.add(identity)
            items.append(normalize(node))
        if len(nodes) < PAGE_SIZE:
            break
        page += 1
    if len(items) != expected_count:
        raise RetrievalError(
            f"{name} item count is incomplete: expected {expected_count}, got {len(items)}"
        )
    return items, {"expected_items": expected_count, "retrieved_items": len(items), "pages": page}


def _paginate_wrapped_rest_list(
    client: GhClient,
    endpoint: str,
    collection_key: str,
    name: str,
    normalize: Callable[[dict[str, Any]], T],
) -> tuple[list[T], dict[str, int]]:
    items: list[T] = []
    page = 1
    expected_count: int | None = None
    seen_items: set[tuple[str, str]] = set()
    while True:
        if page > MAX_PAGES:
            raise RetrievalError(f"Exceeded pagination limit for {name}")
        response = _require_dict(
            client.rest(endpoint, {"per_page": PAGE_SIZE, "page": page}),
            name,
        )
        total_count = response.get("total_count")
        if not isinstance(total_count, int):
            raise RetrievalError(f"GitHub response has no total_count for {name}")
        if expected_count is None:
            expected_count = total_count
        elif expected_count != total_count:
            raise RetrievalError(f"{name} changed during pagination")
        nodes = _require_list(response.get(collection_key), f"{name}.{collection_key}")
        for raw_node in nodes:
            node = _require_dict(raw_node, f"{name}.item")
            identity = _rest_item_identity(node, name)
            if identity in seen_items:
                raise RetrievalError(f"Duplicate item while paginating {name}: {identity[1]}")
            seen_items.add(identity)
            items.append(normalize(node))
        if len(nodes) < PAGE_SIZE:
            break
        page += 1
    if len(items) != expected_count:
        raise RetrievalError(
            f"{name} item count is incomplete: expected {expected_count}, got {len(items)}"
        )
    return items, {"expected_items": expected_count, "retrieved_items": len(items), "pages": page}


def _rest_item_identity(node: dict[str, Any], name: str) -> tuple[str, str]:
    for key in ("id", "sha", "filename"):
        value = node.get(key)
        if isinstance(value, (int, str)):
            return key, str(value)
    raise RetrievalError(f"GitHub response has no stable item identity for {name}")


def _actor(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {key: value.get(key) for key in ("login", "name", "url") if key in value}


def _reviewer(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    result = {
        "type": value.get("__typename"),
        **{key: value.get(key) for key in ("login", "slug", "name", "url") if key in value},
    }
    organization = value.get("organization")
    if isinstance(organization, dict):
        result["organization"] = organization.get("login")
    return result


def _normalize_core(response: dict[str, Any]) -> dict[str, Any]:
    data = _require_dict(response.get("data"), "data")
    viewer = _require_dict(data.get("viewer"), "data.viewer")
    repository = _require_dict(data.get("repository"), "data.repository")
    pull_request = _require_dict(repository.get("pullRequest"), "data.repository.pullRequest")
    count_names = (
        "assignees",
        "labels",
        "reviewRequests",
        "comments",
        "reviews",
        "commits",
        "files",
        "reviewThreads",
    )
    counts: dict[str, int] = {}
    for name in count_names:
        connection = _require_dict(pull_request.get(name), f"pullRequest.{name}")
        total_count = connection.get("totalCount")
        if not isinstance(total_count, int):
            raise RetrievalError(f"GitHub response has no totalCount for pullRequest.{name}")
        counts[name] = total_count
    status_rollup = pull_request.get("statusCheckRollup")
    status_contexts = 0
    if status_rollup is not None:
        status_rollup = _require_dict(status_rollup, "pullRequest.statusCheckRollup")
        contexts = _require_dict(status_rollup.get("contexts"), "statusCheckRollup.contexts")
        status_contexts = contexts.get("totalCount")
        if not isinstance(status_contexts, int):
            raise RetrievalError("GitHub response has no status-check context count")
    counts["statusCheckContexts"] = status_contexts
    latest_review = pull_request.get("viewerLatestReview")
    latest_request = pull_request.get("viewerLatestReviewRequest")
    normalized_latest_review = None
    if isinstance(latest_review, dict):
        normalized_latest_review = {
            "id": latest_review.get("id"),
            "database_id": latest_review.get("fullDatabaseId"),
            "state": latest_review.get("state"),
            "submitted_at": latest_review.get("submittedAt"),
            "commit_id": (latest_review.get("commit") or {}).get("oid"),
        }
    normalized_latest_request = None
    if isinstance(latest_request, dict):
        normalized_latest_request = {
            "id": latest_request.get("id"),
            "as_code_owner": latest_request.get("asCodeOwner"),
            "requested_reviewer": _reviewer(latest_request.get("requestedReviewer")),
        }
    base_repository = pull_request.get("baseRepository") or {}
    head_repository = pull_request.get("headRepository") or {}
    rate_limit = data.get("rateLimit")
    return {
        "viewer": _actor(viewer),
        "repository": {
            "name_with_owner": repository.get("nameWithOwner"),
            "url": repository.get("url"),
        },
        "pull_request": {
            "id": pull_request.get("id"),
            "number": pull_request.get("number"),
            "url": pull_request.get("url"),
            "title": pull_request.get("title"),
            "body": pull_request.get("body"),
            "state": pull_request.get("state"),
            "is_draft": pull_request.get("isDraft"),
            "merged": pull_request.get("merged"),
            "merged_at": pull_request.get("mergedAt"),
            "closed": pull_request.get("closed"),
            "closed_at": pull_request.get("closedAt"),
            "created_at": pull_request.get("createdAt"),
            "updated_at": pull_request.get("updatedAt"),
            "published_at": pull_request.get("publishedAt"),
            "author": _actor(pull_request.get("author")),
            "author_association": pull_request.get("authorAssociation"),
            "base": {
                "ref": pull_request.get("baseRefName"),
                "sha": pull_request.get("baseRefOid"),
                "repository": base_repository.get("nameWithOwner"),
                "repository_url": base_repository.get("url"),
            },
            "head": {
                "ref": pull_request.get("headRefName"),
                "sha": pull_request.get("headRefOid"),
                "repository": head_repository.get("nameWithOwner"),
                "repository_url": head_repository.get("url"),
            },
            "is_cross_repository": pull_request.get("isCrossRepository"),
            "maintainer_can_modify": pull_request.get("maintainerCanModify"),
            "mergeable": pull_request.get("mergeable"),
            "merge_state_status": pull_request.get("mergeStateStatus"),
            "review_decision": pull_request.get("reviewDecision"),
            "viewer_did_author": pull_request.get("viewerDidAuthor"),
            "viewer_latest_review": normalized_latest_review,
            "viewer_latest_review_request": normalized_latest_request,
            "status_check_rollup": None
            if status_rollup is None
            else {"state": status_rollup.get("state"), "total_count": status_contexts},
        },
        "counts": counts,
        "rate_limit": rate_limit,
    }


def _core_fingerprint(core: dict[str, Any]) -> dict[str, Any]:
    pull_request = core["pull_request"]
    latest_review = pull_request.get("viewer_latest_review") or {}
    latest_request = pull_request.get("viewer_latest_review_request") or {}
    return {
        "base_sha": pull_request["base"]["sha"],
        "head_sha": pull_request["head"]["sha"],
        "state": pull_request["state"],
        "is_draft": pull_request["is_draft"],
        "merged": pull_request["merged"],
        "updated_at": pull_request["updated_at"],
        "mergeable": pull_request["mergeable"],
        "merge_state_status": pull_request["merge_state_status"],
        "review_decision": pull_request["review_decision"],
        "viewer_latest_review_id": latest_review.get("id"),
        "viewer_latest_review_request_id": latest_request.get("id"),
        "status_check_rollup": pull_request.get("status_check_rollup"),
        "counts": core["counts"],
    }


def _normalize_assignee(node: dict[str, Any]) -> dict[str, Any]:
    return _actor(node) or {}


def _normalize_label(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": node.get("name"),
        "color": node.get("color"),
        "description": node.get("description"),
    }


def _normalize_review_request(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node.get("id"),
        "as_code_owner": node.get("asCodeOwner"),
        "requested_reviewer": _reviewer(node.get("requestedReviewer")),
    }


def _normalize_comment(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node.get("id"),
        "database_id": node.get("fullDatabaseId"),
        "author": _actor(node.get("author")),
        "author_association": node.get("authorAssociation"),
        "body": node.get("body"),
        "created_at": node.get("createdAt"),
        "updated_at": node.get("updatedAt"),
        "url": node.get("url"),
        "is_minimized": node.get("isMinimized"),
        "minimized_reason": node.get("minimizedReason"),
        "viewer_did_author": node.get("viewerDidAuthor"),
    }


def _normalize_review(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": node.get("id"),
        "database_id": node.get("fullDatabaseId"),
        "author": _actor(node.get("author")),
        "author_association": node.get("authorAssociation"),
        "body": node.get("body"),
        "state": node.get("state"),
        "submitted_at": node.get("submittedAt"),
        "created_at": node.get("createdAt"),
        "updated_at": node.get("updatedAt"),
        "url": node.get("url"),
        "viewer_did_author": node.get("viewerDidAuthor"),
        "commit_id": (node.get("commit") or {}).get("oid"),
        "comment_count": (node.get("comments") or {}).get("totalCount"),
    }


def _normalize_thread_comment(node: dict[str, Any]) -> dict[str, Any]:
    review = node.get("pullRequestReview") or {}
    reply_to = node.get("replyTo") or {}
    return {
        "id": node.get("id"),
        "database_id": node.get("fullDatabaseId"),
        "author": _actor(node.get("author")),
        "author_association": node.get("authorAssociation"),
        "body": node.get("body"),
        "state": node.get("state"),
        "created_at": node.get("createdAt"),
        "updated_at": node.get("updatedAt"),
        "published_at": node.get("publishedAt"),
        "url": node.get("url"),
        "path": node.get("path"),
        "line": node.get("line"),
        "start_line": node.get("startLine"),
        "original_line": node.get("originalLine"),
        "original_start_line": node.get("originalStartLine"),
        "outdated": node.get("outdated"),
        "diff_hunk": node.get("diffHunk"),
        "viewer_did_author": node.get("viewerDidAuthor"),
        "reply_to": None
        if not reply_to
        else {"id": reply_to.get("id"), "database_id": reply_to.get("fullDatabaseId")},
        "review": None
        if not review
        else {
            "id": review.get("id"),
            "database_id": review.get("fullDatabaseId"),
            "state": review.get("state"),
            "submitted_at": review.get("submittedAt"),
            "author": _actor(review.get("author")),
            "commit_id": (review.get("commit") or {}).get("oid"),
        },
    }


def _normalize_thread(node: dict[str, Any], comments: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": node.get("id"),
        "is_collapsed": node.get("isCollapsed"),
        "is_outdated": node.get("isOutdated"),
        "is_resolved": node.get("isResolved"),
        "path": node.get("path"),
        "line": node.get("line"),
        "start_line": node.get("startLine"),
        "original_line": node.get("originalLine"),
        "original_start_line": node.get("originalStartLine"),
        "diff_side": node.get("diffSide"),
        "start_diff_side": node.get("startDiffSide"),
        "subject_type": node.get("subjectType"),
        "viewer_can_reply": node.get("viewerCanReply"),
        "viewer_can_resolve": node.get("viewerCanResolve"),
        "viewer_can_unresolve": node.get("viewerCanUnresolve"),
        "resolved_by": _actor(node.get("resolvedBy")),
        "comments": comments,
    }


def _fetch_remaining_thread_comments(
    client: GhClient,
    thread_id: str,
    connection: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    expected_count = connection.get("totalCount")
    if not isinstance(expected_count, int):
        raise RetrievalError(f"Review thread {thread_id} has no comment totalCount")
    raw_comments = _require_list(connection.get("nodes"), f"thread {thread_id} comments")
    comments = [
        _normalize_thread_comment(_require_dict(item, "thread comment"))
        for item in raw_comments
    ]
    pages = 1
    has_next, cursor = _page_info(connection, f"thread {thread_id} comments")
    seen_ids = {comment["id"] for comment in comments if isinstance(comment.get("id"), str)}
    while has_next:
        if pages >= MAX_PAGES:
            raise RetrievalError(f"Exceeded pagination limit for thread {thread_id} comments")
        response = client.graphql(THREAD_COMMENTS_QUERY, {"id": thread_id, "cursor": cursor})
        data = _require_dict(response.get("data"), "data")
        node = _require_dict(data.get("node"), "review thread")
        if node.get("id") != thread_id:
            raise RetrievalError(f"GitHub returned the wrong review thread for {thread_id}")
        next_connection = _require_dict(node.get("comments"), "review thread comments")
        if next_connection.get("totalCount") != expected_count:
            raise RetrievalError(f"Review thread {thread_id} changed during pagination")
        next_nodes = _require_list(next_connection.get("nodes"), "review thread comments")
        for raw_node in next_nodes:
            comment = _normalize_thread_comment(_require_dict(raw_node, "thread comment"))
            comment_id = comment.get("id")
            if isinstance(comment_id, str) and comment_id in seen_ids:
                raise RetrievalError(f"Duplicate comment while paginating thread {thread_id}")
            if isinstance(comment_id, str):
                seen_ids.add(comment_id)
            comments.append(comment)
        pages += 1
        has_next, cursor = _page_info(next_connection, f"thread {thread_id} comments")
    if len(comments) != expected_count:
        raise RetrievalError(
            f"Review thread {thread_id} comments are incomplete: "
            f"expected {expected_count}, got {len(comments)}"
        )
    return comments, pages


def fetch_review_threads(
    client: GhClient,
    pull_request_id: str,
    expected_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    threads: list[dict[str, Any]] = []
    cursor: str | None = None
    pages = 0
    seen_ids: set[str] = set()
    comment_completeness: list[dict[str, Any]] = []
    while True:
        if pages >= MAX_PAGES:
            raise RetrievalError("Exceeded pagination limit for review threads")
        response = client.graphql(
            REVIEW_THREADS_QUERY,
            {"id": pull_request_id, "cursor": cursor},
        )
        connection = _connection_from_node(response, "reviewThreads")
        if connection.get("totalCount") != expected_count:
            raise RetrievalError("Review-thread count changed or is incomplete")
        nodes = _require_list(connection.get("nodes"), "reviewThreads.nodes")
        for raw_node in nodes:
            node = _require_dict(raw_node, "review thread")
            thread_id = node.get("id")
            if not isinstance(thread_id, str):
                raise RetrievalError("Review thread has no node ID")
            if thread_id in seen_ids:
                raise RetrievalError(f"Duplicate review thread: {thread_id}")
            seen_ids.add(thread_id)
            comments_connection = _require_dict(node.get("comments"), "review thread comments")
            comments, comment_pages = _fetch_remaining_thread_comments(
                client,
                thread_id,
                comments_connection,
            )
            threads.append(_normalize_thread(node, comments))
            comment_completeness.append(
                {
                    "thread_id": thread_id,
                    "expected_items": comments_connection.get("totalCount"),
                    "retrieved_items": len(comments),
                    "pages": comment_pages,
                }
            )
        pages += 1
        has_next, cursor = _page_info(connection, "reviewThreads")
        if not has_next:
            break
    if len(threads) != expected_count:
        raise RetrievalError(
            f"Review threads are incomplete: expected {expected_count}, got {len(threads)}"
        )
    return threads, {
        "expected_items": expected_count,
        "retrieved_items": len(threads),
        "pages": pages,
        "comments": comment_completeness,
    }


def _normalize_thread_state(node: dict[str, Any]) -> dict[str, Any]:
    comments = _require_dict(node.get("comments"), "thread-state comments")
    latest_nodes = _require_list(comments.get("nodes"), "thread-state latest comment")
    latest = latest_nodes[0] if latest_nodes else None
    return {
        "id": node.get("id"),
        "is_collapsed": node.get("isCollapsed"),
        "is_outdated": node.get("isOutdated"),
        "is_resolved": node.get("isResolved"),
        "path": node.get("path"),
        "line": node.get("line"),
        "start_line": node.get("startLine"),
        "comment_count": comments.get("totalCount"),
        "latest_comment": None
        if latest is None
        else {
            "id": latest.get("id"),
            "state": latest.get("state"),
            "updated_at": latest.get("updatedAt"),
        },
    }


def _thread_state_from_full(thread: dict[str, Any]) -> dict[str, Any]:
    comments = thread["comments"]
    latest = comments[-1] if comments else None
    return {
        "id": thread.get("id"),
        "is_collapsed": thread.get("is_collapsed"),
        "is_outdated": thread.get("is_outdated"),
        "is_resolved": thread.get("is_resolved"),
        "path": thread.get("path"),
        "line": thread.get("line"),
        "start_line": thread.get("start_line"),
        "comment_count": len(comments),
        "latest_comment": None
        if latest is None
        else {
            "id": latest.get("id"),
            "state": latest.get("state"),
            "updated_at": latest.get("updated_at"),
        },
    }


def _normalize_commit(node: dict[str, Any]) -> dict[str, Any]:
    commit = node.get("commit") or {}
    author = node.get("author") or {}
    committer = node.get("committer") or {}
    return {
        "sha": node.get("sha"),
        "url": node.get("html_url"),
        "message": commit.get("message"),
        "authored_at": (commit.get("author") or {}).get("date"),
        "committed_at": (commit.get("committer") or {}).get("date"),
        "author": author.get("login"),
        "committer": committer.get("login"),
        "parents": [
            parent.get("sha")
            for parent in node.get("parents", [])
            if isinstance(parent, dict)
        ],
    }


def _normalize_file(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": node.get("filename"),
        "previous_path": node.get("previous_filename"),
        "status": node.get("status"),
        "additions": node.get("additions"),
        "deletions": node.get("deletions"),
        "changes": node.get("changes"),
        "blob_url": node.get("blob_url"),
        "raw_url": node.get("raw_url"),
    }


def _normalize_check_run(node: dict[str, Any]) -> dict[str, Any]:
    app = node.get("app") or {}
    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "status": node.get("status"),
        "conclusion": node.get("conclusion"),
        "started_at": node.get("started_at"),
        "completed_at": node.get("completed_at"),
        "details_url": node.get("details_url"),
        "external_id": node.get("external_id"),
        "head_sha": node.get("head_sha"),
        "app": {"id": app.get("id"), "slug": app.get("slug"), "name": app.get("name")},
    }


def _normalize_status(node: dict[str, Any]) -> dict[str, Any]:
    creator = node.get("creator") or {}
    return {
        "id": node.get("id"),
        "context": node.get("context"),
        "state": node.get("state"),
        "description": node.get("description"),
        "target_url": node.get("target_url"),
        "created_at": node.get("created_at"),
        "updated_at": node.get("updated_at"),
        "creator": creator.get("login"),
    }


def _latest_submitted_review(
    reviews: list[dict[str, Any]],
    viewer_login: str,
) -> dict[str, Any] | None:
    candidates = [
        review
        for review in reviews
        if (review.get("author") or {}).get("login") == viewer_login
        and review.get("submitted_at")
        and review.get("state") != "PENDING"
    ]
    return max(candidates, key=lambda review: review["submitted_at"], default=None)


def collect_context(target: PullRequestTarget, client: GhClient | None = None) -> dict[str, Any]:
    api = client or GhClient(target.hostname)
    variables = {
        "owner": target.owner,
        "repository": target.repository,
        "number": target.number,
    }
    core_start = _normalize_core(api.graphql(CORE_QUERY, variables))
    actual_repository = core_start["repository"]["name_with_owner"]
    if (
        actual_repository is None
        or actual_repository.casefold() != target.name_with_owner.casefold()
    ):
        raise RetrievalError(
            f"GitHub resolved {target.name_with_owner} as {actual_repository or 'nothing'}"
        )
    pull_request = core_start["pull_request"]
    pull_request_id = pull_request.get("id")
    head_sha = (pull_request.get("head") or {}).get("sha")
    if not isinstance(pull_request_id, str) or not isinstance(head_sha, str):
        raise RetrievalError("GitHub response is missing the PR node ID or head SHA")
    counts = core_start["counts"]
    completeness: dict[str, Any] = {}
    assignees, completeness["assignees"] = _paginate_graphql_connection(
        api,
        ASSIGNEES_QUERY,
        pull_request_id,
        "assignees",
        counts["assignees"],
        _normalize_assignee,
    )
    labels, completeness["labels"] = _paginate_graphql_connection(
        api,
        LABELS_QUERY,
        pull_request_id,
        "labels",
        counts["labels"],
        _normalize_label,
    )
    review_requests, completeness["review_requests"] = _paginate_graphql_connection(
        api,
        REVIEW_REQUESTS_QUERY,
        pull_request_id,
        "reviewRequests",
        counts["reviewRequests"],
        _normalize_review_request,
    )
    comments, completeness["comments"] = _paginate_graphql_connection(
        api,
        COMMENTS_QUERY,
        pull_request_id,
        "comments",
        counts["comments"],
        _normalize_comment,
    )
    reviews, completeness["reviews"] = _paginate_graphql_connection(
        api,
        REVIEWS_QUERY,
        pull_request_id,
        "reviews",
        counts["reviews"],
        _normalize_review,
    )
    review_threads, completeness["review_threads"] = fetch_review_threads(
        api,
        pull_request_id,
        counts["reviewThreads"],
    )
    commits, completeness["commits"] = _paginate_rest_list(
        api,
        f"repos/{target.owner}/{target.repository}/pulls/{target.number}/commits",
        "commits",
        counts["commits"],
        _normalize_commit,
    )
    files, completeness["files"] = _paginate_rest_list(
        api,
        f"repos/{target.owner}/{target.repository}/pulls/{target.number}/files",
        "files",
        counts["files"],
        _normalize_file,
    )
    check_runs, completeness["check_runs"] = _paginate_wrapped_rest_list(
        api,
        f"repos/{target.owner}/{target.repository}/commits/{head_sha}/check-runs",
        "check_runs",
        "check runs",
        _normalize_check_run,
    )
    statuses, completeness["statuses"] = _paginate_wrapped_rest_list(
        api,
        f"repos/{target.owner}/{target.repository}/commits/{head_sha}/status",
        "statuses",
        "commit statuses",
        _normalize_status,
    )
    start_fingerprint = _core_fingerprint(core_start)
    thread_states, completeness["thread_state_readback"] = _paginate_graphql_connection(
        api,
        THREAD_STATES_QUERY,
        pull_request_id,
        "reviewThreads",
        counts["reviewThreads"],
        _normalize_thread_state,
    )
    collected_thread_states = [_thread_state_from_full(thread) for thread in review_threads]
    if sorted(collected_thread_states, key=lambda state: state["id"]) != sorted(
        thread_states,
        key=lambda state: state["id"],
    ):
        raise RetrievalError("Review-thread state changed during retrieval; rerun the collector")
    core_end = _normalize_core(api.graphql(CORE_QUERY, variables))
    end_fingerprint = _core_fingerprint(core_end)
    if start_fingerprint != end_fingerprint:
        raise RetrievalError("Pull-request state changed during retrieval; rerun the collector")
    viewer_login = (core_end.get("viewer") or {}).get("login")
    if not isinstance(viewer_login, str):
        raise RetrievalError("GitHub response is missing the authenticated viewer login")
    pending_reviews = [
        review
        for review in reviews
        if (review.get("author") or {}).get("login") == viewer_login
        and review.get("state") == "PENDING"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "target": {
            "hostname": target.hostname,
            "repository": target.name_with_owner,
            "number": target.number,
        },
        "viewer": core_end["viewer"],
        "repository": core_end["repository"],
        "pull_request": core_end["pull_request"],
        "assignees": assignees,
        "labels": labels,
        "review_requests": review_requests,
        "comments": comments,
        "reviews": reviews,
        "review_threads": review_threads,
        "commits": commits,
        "files": files,
        "checks": {"check_runs": check_runs, "statuses": statuses},
        "derived": {
            "latest_submitted_review_by_viewer": _latest_submitted_review(reviews, viewer_login),
            "pending_reviews_by_viewer": pending_reviews,
            "viewer_has_outstanding_review_request": core_end["pull_request"].get(
                "viewer_latest_review_request"
            )
            is not None,
            "unresolved_thread_ids": [
                thread["id"] for thread in review_threads if not thread["is_resolved"]
            ],
            "unresolved_current_thread_ids": [
                thread["id"]
                for thread in review_threads
                if not thread["is_resolved"] and not thread["is_outdated"]
            ],
        },
        "completeness": {
            "consistent_snapshot": True,
            "start_fingerprint": start_fingerprint,
            "end_fingerprint": end_fingerprint,
            "collections": completeness,
        },
        "rate_limit": {"start": core_start.get("rate_limit"), "end": core_end.get("rate_limit")},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch complete, read-only GitHub pull-request context as JSON."
    )
    parser.add_argument(
        "target",
        help="OWNER/REPOSITORY#NUMBER or a GitHub pull-request URL",
    )
    parser.add_argument(
        "--hostname",
        default="github.com",
        help="GitHub hostname for shorthand targets (default: github.com)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        target = PullRequestTarget.parse(arguments.target, arguments.hostname)
        context = collect_context(target)
    except RetrievalError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    try:
        json.dump(context, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
