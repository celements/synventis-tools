# GitHub workflow

## Contents

- [Retrieve complete context](#retrieve-complete-context)
- [Inspect the pinned change locally](#inspect-the-pinned-change-locally)
- [Select a follow-up baseline](#select-a-follow-up-baseline)
- [Prepare mutations](#prepare-mutations)
- [Apply authorized mutations](#apply-authorized-mutations)
- [Handle partial failure](#handle-partial-failure)

## Retrieve complete context

Run:

```bash
python3 <skill-directory>/scripts/fetch_pr_context.py OWNER/REPOSITORY#NUMBER
```

The script uses authenticated `gh api` calls, emits one JSON document to stdout, and performs no
mutation. It collects normalized PR state, exact base and head SHAs, authenticated viewer, commits,
changed-file metadata, checks and statuses, reviews, top-level comments, labels, assignees, requested
reviewers, and every review thread and reply with current resolved and outdated state. It records a
schema version, timestamp, page and item counts, and start/end snapshot fingerprints.

Treat a nonzero exit as no usable snapshot. Do not salvage partial stdout or bypass the failure with
an unpaginated command. Keep fetched bodies ephemeral by default; never persist credentials. A
GitHub connector may add evidence but cannot replace this completeness gate.

Verify the target namespace before following a same-number PR or issue mentioned in a thread.

## Inspect the pinned change locally

Fetch the exact base and head commits and use local Git for the authoritative three-dot diff. Do not
assume an API `patch` field covers large or binary changes.

Never switch, reset, clean, or build in a user's active dirty checkout. Reuse it only when it is
already at the exact reviewed head and every required command is guaranteed not to disturb tracked
or untracked work. Otherwise:

1. Create a unique temporary directory.
2. Add a detached worktree for an existing repository, or clone temporarily when the repository is
   absent.
3. Inspect build and setup scripts before executing them.
4. Install dependencies only through the locked documented project mechanism, within the isolated
   checkout. Do not install global tools or update lockfiles.
5. Verify cleanup-target identity and worktree cleanliness.
6. Remove only the dedicated temporary worktree or clone when no required artifact remains.

If the head changes during read-only review, incorporate the new delta before reporting. If it keeps
changing, return a provisional report tied to the last inspected SHA and withhold the verdict.

If the PR closes or merges during review, stop every pending mutation. Continue only as explicitly
requested or materially useful historical analysis, and label it as historical rather than a current
merge verdict.

Treat unresolved merge conflicts as a lifecycle blocker: provisional inspection is allowed, but
withhold the final verdict because conflict resolution changes the effective diff.

## Select a follow-up baseline

Use this priority for `changes since my last review`:

1. A SHA explicitly supplied by the user.
2. The latest submitted review `commit_id` from the authenticated reviewer.
3. A previously recorded baseline that is still verifiable.

Confirm that `my` matches the authenticated GitHub viewer. Ask if identity or candidates conflict.
If the baseline is not an ancestor of the current head, do not substitute a convenient ancestor.
Reconstruct the current `base...head` review, compare with a prior snapshot where available, and
fully reassess rewritten or unverifiable areas.

Drive a follow-up from new commits, every new comment or reply, and current thread state. Reinspect
previously reviewed code only when the delta or new context can affect it. GitHub's `resolved` and
`outdated` fields are workflow state, not proof that a finding was addressed.

## Prepare mutations

Refetch complete GitHub and Jira state immediately before any mutation. Compare head, effective
base, contract, checks, review decision, comments, and threads with the reviewed snapshot. Reassess
and request renewed authorization after any material change.

Protect an existing pending review from the authenticated user. Do not append, submit, or discard it
without asking whether to use it.

Prefer a valid line-anchored inline comment for each concrete code finding. Use a review summary only
for the verdict, a cross-cutting issue with no honest anchor, and validation limitations. Do not
duplicate a finding inline and in the summary.

Batch validated initial comments into one review with exactly one event: `APPROVE`,
`REQUEST_CHANGES`, or `COMMENT`. Put follow-up replies in their existing threads. Treat posting a
reply and resolving a thread as separate mutations. Correct materially wrong prior claims with a
concise reply before resolving when both actions are authorized.

Read another human reviewer's thread as evidence, but do not speak for, correct, or resolve it unless
the user explicitly requests that action and has appropriate authority.

Do not add an AI signature or agent branding. Match the established language of the PR or thread
unless the user requests another language. Keep public PR text technical; keep apology, motives, and
process discussion in a separately requested private-channel draft.

## Apply authorized mutations

Mutation authorization is operation-specific. Authorization for one operation does not authorize
another, with only these explicit workflow couplings:

- Requesting an individual reviewer also adds the same person as an assignee. Team review requests
  do not imply an assignee.
- Submitting any review event in response to an outstanding review request removes the authenticated
  reviewer from the PR's assignees. Do not self-unassign when there was no outstanding request.

Assignees and requested reviewers otherwise remain independent. Preserve all unrelated values and
verify both fields afterward.

A conditional multi-PR instruction such as `approve every named PR with no open findings` is valid
when the candidate set and condition are objective. Revalidate each PR, mutate only qualifying PRs,
and report affected and excluded PRs.

Do not submit `APPROVE` or `REQUEST_CHANGES` when the authenticated viewer authored the PR. A full
read-only self-review and an authorized `COMMENT` are allowed; label the conclusion as self-review.

After mutation, read back at least the current base and head, PR state, checks, review decision,
unresolved threads, assignees, requested reviewers, and the created review/comments. Report the
observed live state rather than assuming API success means workflow completion.

## Handle partial failure

After any failing mutation:

1. Stop the mutation sequence.
2. Refetch live state.
3. Report exactly what succeeded, failed, and was not attempted.
4. Do not retry an operation that could duplicate a comment or review.
5. Continue only when the remaining operation is demonstrably idempotent or newly authorized.
