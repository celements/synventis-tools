from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "fetch_pr_context.py"
SPEC = importlib.util.spec_from_file_location("fetch_pr_context", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
fetch_pr_context = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fetch_pr_context
SPEC.loader.exec_module(fetch_pr_context)


class FakeGraphqlClient:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def graphql(self, query, variables):
        self.calls.append((query, variables.copy()))
        return self.handler(query, variables)


class FakeRestClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def rest(self, endpoint, fields):
        self.calls.append((endpoint, fields.copy()))
        return self.responses[fields["page"] - 1]


def connection_response(name, nodes, total_count, has_next=False, cursor=None):
    return {
        "data": {
            "node": {
                name: {
                    "totalCount": total_count,
                    "nodes": nodes,
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                }
            }
        }
    }


def thread_comment(index):
    return {
        "id": f"comment-{index}",
        "fullDatabaseId": str(index),
        "author": {"login": "author", "url": "https://example.invalid/author"},
        "body": f"comment {index}",
        "state": "SUBMITTED",
        "createdAt": f"2026-01-01T00:00:{index % 60:02d}Z",
        "updatedAt": f"2026-01-01T00:00:{index % 60:02d}Z",
        "publishedAt": f"2026-01-01T00:00:{index % 60:02d}Z",
        "url": f"https://example.invalid/comments/{index}",
        "path": "src/example.py",
        "line": index + 1,
        "startLine": None,
        "originalLine": index + 1,
        "originalStartLine": None,
        "outdated": False,
        "diffHunk": "@@ synthetic @@",
        "viewerDidAuthor": False,
        "replyTo": None,
        "pullRequestReview": None,
    }


def review_thread(index, comments=None, has_next=False, cursor=None, total_count=None):
    comment_nodes = comments or []
    return {
        "id": f"thread-{index}",
        "isCollapsed": False,
        "isOutdated": False,
        "isResolved": False,
        "path": "src/example.py",
        "line": index + 1,
        "startLine": None,
        "originalLine": index + 1,
        "originalStartLine": None,
        "diffSide": "RIGHT",
        "startDiffSide": None,
        "subjectType": "LINE",
        "viewerCanReply": True,
        "viewerCanResolve": True,
        "viewerCanUnresolve": False,
        "resolvedBy": None,
        "comments": {
            "totalCount": len(comment_nodes) if total_count is None else total_count,
            "nodes": comment_nodes,
            "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
        },
    }


def commit_node(index):
    sha = f"sha-{index:03d}"
    parent = [] if index == 0 else [{"sha": f"sha-{index - 1:03d}"}]
    return {
        "sha": sha,
        "html_url": f"https://example.invalid/commit/{sha}",
        "commit": {
            "message": f"commit {index}",
            "author": {"date": "2026-01-01T00:00:00Z"},
            "committer": {"date": "2026-01-01T00:00:00Z"},
        },
        "author": {"login": "author"},
        "committer": {"login": "committer"},
        "parents": parent,
    }


class PullRequestTargetTest(unittest.TestCase):
    def test_parses_reference(self):
        target = fetch_pr_context.PullRequestTarget.parse("acme/widgets#42")
        self.assertEqual("github.com", target.hostname)
        self.assertEqual("acme/widgets", target.name_with_owner)
        self.assertEqual(42, target.number)

    def test_parses_url(self):
        target = fetch_pr_context.PullRequestTarget.parse(
            "https://git.example.test/acme/widgets/pull/42/files"
        )
        self.assertEqual("git.example.test", target.hostname)
        self.assertEqual("acme/widgets", target.name_with_owner)
        self.assertEqual(42, target.number)

    def test_rejects_ambiguous_number(self):
        with self.assertRaises(fetch_pr_context.RetrievalError):
            fetch_pr_context.PullRequestTarget.parse("42")


class PaginationTest(unittest.TestCase):
    def test_paginates_graphql_connection(self):
        first_page = [{"id": f"item-{index}"} for index in range(100)]
        second_page = [{"id": "item-100"}]

        def handler(_query, variables):
            if variables["cursor"] is None:
                return connection_response("items", first_page, 101, True, "next")
            return connection_response("items", second_page, 101)

        client = FakeGraphqlClient(handler)
        items, completeness = fetch_pr_context._paginate_graphql_connection(
            client,
            "query FetchItems {}",
            "pull-request-id",
            "items",
            101,
            lambda node: node,
        )
        self.assertEqual(101, len(items))
        self.assertEqual(2, completeness["pages"])
        self.assertEqual([None, "next"], [call[1]["cursor"] for call in client.calls])

    def test_paginates_threads_and_every_reply(self):
        initial_comments = [thread_comment(index) for index in range(100)]
        first_threads = [
            review_thread(
                0,
                initial_comments,
                has_next=True,
                cursor="comment-page-2",
                total_count=101,
            )
        ] + [review_thread(index) for index in range(1, 100)]
        final_thread = review_thread(100)

        def handler(query, variables):
            if "FetchReviewThreadComments" in query:
                self.assertEqual("thread-0", variables["id"])
                self.assertEqual("comment-page-2", variables["cursor"])
                return {
                    "data": {
                        "node": {
                            "id": "thread-0",
                            "comments": {
                                "totalCount": 101,
                                "nodes": [thread_comment(100)],
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                            },
                        }
                    }
                }
            if variables["cursor"] is None:
                return connection_response(
                    "reviewThreads",
                    first_threads,
                    101,
                    True,
                    "thread-page-2",
                )
            return connection_response("reviewThreads", [final_thread], 101)

        client = FakeGraphqlClient(handler)
        threads, completeness = fetch_pr_context.fetch_review_threads(
            client,
            "pull-request-id",
            101,
        )
        self.assertEqual(101, len(threads))
        self.assertEqual(101, len(threads[0]["comments"]))
        self.assertEqual(2, completeness["pages"])
        self.assertEqual(2, completeness["comments"][0]["pages"])

    def test_paginates_rest_list(self):
        first_page = [{"sha": f"sha-{index}"} for index in range(100)]
        second_page = [{"sha": "sha-100"}]
        client = FakeRestClient([first_page, second_page])
        items, completeness = fetch_pr_context._paginate_rest_list(
            client,
            "repos/acme/widgets/pulls/42/commits",
            "commits",
            101,
            lambda node: node,
        )
        self.assertEqual(101, len(items))
        self.assertEqual(2, completeness["pages"])
        self.assertEqual([1, 2], [call[1]["page"] for call in client.calls])

    def test_rejects_duplicate_rest_items(self):
        first_page = [{"sha": f"sha-{index}"} for index in range(100)]
        second_page = [{"sha": "sha-0"}]
        client = FakeRestClient([first_page, second_page])
        with self.assertRaisesRegex(fetch_pr_context.RetrievalError, "Duplicate item"):
            fetch_pr_context._paginate_rest_list(
                client,
                "repos/acme/widgets/pulls/42/commits",
                "commits",
                101,
                lambda node: node,
            )

    def test_allows_different_files_with_same_blob_sha(self):
        first_page = [
            {"filename": f"src/file-{index}.ts", "sha": f"sha-{index}"}
            for index in range(100)
        ]
        second_page = [{"filename": "src/copy.ts", "sha": "sha-0"}]
        client = FakeRestClient([first_page, second_page])
        items, completeness = fetch_pr_context._paginate_rest_list(
            client,
            "repos/acme/widgets/pulls/42/files",
            "files",
            101,
            lambda node: node,
        )
        self.assertEqual(101, len(items))
        self.assertEqual(101, completeness["retrieved_items"])

    def test_paginates_wrapped_rest_list(self):
        first_page = {
            "total_count": 101,
            "check_runs": [{"id": index} for index in range(100)],
        }
        second_page = {"total_count": 101, "check_runs": [{"id": 100}]}
        client = FakeRestClient([first_page, second_page])
        items, completeness = fetch_pr_context._paginate_wrapped_rest_list(
            client,
            "repos/acme/widgets/commits/sha/check-runs",
            "check_runs",
            "check runs",
            lambda node: node,
        )
        self.assertEqual(101, len(items))
        self.assertEqual(2, completeness["pages"])

    def test_fails_when_next_cursor_is_missing(self):
        client = FakeGraphqlClient(
            lambda _query, _variables: connection_response(
                "items",
                [{"id": "item-0"}],
                2,
                True,
                None,
            )
        )
        with self.assertRaisesRegex(fetch_pr_context.RetrievalError, "endCursor"):
            fetch_pr_context._paginate_graphql_connection(
                client,
                "query FetchItems {}",
                "pull-request-id",
                "items",
                2,
                lambda node: node,
            )

    def test_fails_when_reported_count_is_incomplete(self):
        client = FakeGraphqlClient(
            lambda _query, _variables: connection_response(
                "items",
                [{"id": "item-0"}],
                1,
            )
        )
        with self.assertRaisesRegex(fetch_pr_context.RetrievalError, "expected 2"):
            fetch_pr_context._paginate_graphql_connection(
                client,
                "query FetchItems {}",
                "pull-request-id",
                "items",
                2,
                lambda node: node,
            )

    def test_fails_on_malformed_connection(self):
        client = FakeGraphqlClient(lambda _query, _variables: {"data": {"node": {}}})
        with self.assertRaisesRegex(fetch_pr_context.RetrievalError, "data.node.items"):
            fetch_pr_context._paginate_graphql_connection(
                client,
                "query FetchItems {}",
                "pull-request-id",
                "items",
                0,
                lambda node: node,
            )


class CommitCollectionTest(unittest.TestCase):
    def setUp(self):
        self.target = fetch_pr_context.PullRequestTarget.parse("acme/widgets#42")
        self.pull_request = {
            "base": {"ref": "main", "sha": "base-sha"},
            "head": {"ref": "feature", "sha": "head-sha"},
        }

    def test_uses_pull_request_endpoint_through_250_commits(self):
        client = FakeRestClient([[commit_node(0), commit_node(1)]])

        commits, completeness = fetch_pr_context._fetch_commits(
            client,
            self.target,
            self.pull_request,
            2,
        )

        self.assertEqual(2, len(commits))
        self.assertEqual("pull_request_api", completeness["source"])
        self.assertEqual(
            "repos/acme/widgets/pulls/42/commits",
            client.calls[0][0],
        )

    def test_prefers_git_for_more_than_250_commits(self):
        git_commits = [commit_node(index) for index in range(251)]
        git_completeness = {
            "expected_items": 251,
            "retrieved_items": 251,
            "pages": 0,
            "source": "git",
        }
        client = FakeRestClient([])
        with patch.object(
            fetch_pr_context,
            "_collect_commits_with_git",
            return_value=(git_commits, git_completeness),
        ) as collect_with_git:
            commits, completeness = fetch_pr_context._fetch_commits(
                client,
                self.target,
                self.pull_request,
                251,
            )

        self.assertEqual(251, len(commits))
        self.assertEqual("git", completeness["source"])
        self.assertEqual([], client.calls)
        collect_with_git.assert_called_once_with(self.target, self.pull_request, 251)

    def test_falls_back_to_paginated_compare_api_when_git_is_unavailable(self):
        responses = [
            {"total_commits": 251, "commits": [commit_node(index) for index in range(100)]},
            {
                "total_commits": 251,
                "commits": [commit_node(index) for index in range(100, 200)],
            },
            {
                "total_commits": 251,
                "commits": [commit_node(index) for index in range(200, 251)],
            },
        ]
        client = FakeRestClient(responses)
        with patch.object(
            fetch_pr_context,
            "_collect_commits_with_git",
            side_effect=fetch_pr_context.LocalGitUnavailable("git CLI is unavailable"),
        ):
            commits, completeness = fetch_pr_context._fetch_commits(
                client,
                self.target,
                self.pull_request,
                251,
            )

        self.assertEqual(251, len(commits))
        self.assertEqual("compare_api", completeness["source"])
        self.assertEqual(3, completeness["pages"])
        self.assertEqual("git CLI is unavailable", completeness["git_fallback_reason"])
        self.assertEqual([1, 2, 3], [call[1]["page"] for call in client.calls])
        self.assertEqual(
            {"repos/acme/widgets/compare/base-sha...head-sha"},
            {call[0] for call in client.calls},
        )

    def test_compare_api_fails_closed_when_count_does_not_match(self):
        client = FakeRestClient([{"total_commits": 250, "commits": [commit_node(0)]}])
        with patch.object(
            fetch_pr_context,
            "_collect_commits_with_git",
            side_effect=fetch_pr_context.LocalGitUnavailable("git CLI is unavailable"),
        ), self.assertRaisesRegex(fetch_pr_context.RetrievalError, "expected 251"):
            fetch_pr_context._fetch_commits(
                client,
                self.target,
                self.pull_request,
                251,
            )

    def test_git_collector_fetches_pinned_refs_and_reads_exact_range(self):
        base_sha = "b" * 40
        first_sha = "1" * 40
        head_sha = "h" * 40
        pull_request = {
            "base": {"ref": "main", "sha": base_sha},
            "head": {"ref": "feature", "sha": head_sha},
        }
        git_output = "\0".join(
            [
                first_sha,
                base_sha,
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
                "first commit\n",
                head_sha,
                first_sha,
                "2026-01-02T00:00:00+00:00",
                "2026-01-02T00:00:00+00:00",
                "second commit\n",
            ]
        )
        with patch.object(
            fetch_pr_context.shutil,
            "which",
            return_value="/usr/bin/git",
        ), patch.object(
            fetch_pr_context,
            "_run_git",
            side_effect=["", "", f"{base_sha}\n", f"{head_sha}\n", git_output],
        ) as run_git:
            commits, completeness = fetch_pr_context._collect_commits_with_git(
                self.target,
                pull_request,
                2,
            )

        self.assertEqual([first_sha, head_sha], [commit["sha"] for commit in commits])
        self.assertEqual("second commit", commits[-1]["message"])
        self.assertEqual("git", completeness["source"])
        fetch_arguments = run_git.call_args_list[1].args[0]
        self.assertIn("+refs/heads/main:refs/synventis/base", fetch_arguments)
        self.assertIn("+refs/pull/42/head:refs/synventis/head", fetch_arguments)


class FailClosedCliTest(unittest.TestCase):
    def test_retrieval_failure_emits_no_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(
            fetch_pr_context,
            "collect_context",
            side_effect=fetch_pr_context.RetrievalError("incomplete review threads"),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            result = fetch_pr_context.main(["acme/widgets#42"])
        self.assertEqual(1, result)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("incomplete review threads", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
