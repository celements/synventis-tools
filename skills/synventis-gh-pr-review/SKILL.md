---
name: synventis-gh-pr-review
description: Review GitHub pull requests for Synventis, Celements, and ProgOnline repositories using complete live GitHub conversations and authoritative Jira contracts. Use for initial PR reviews, Jira-linked reviews, changes since a prior review, author replies or pushback, connected multi-repository changes, requests involving draft or WIP markers, thread cleanup, approval or request-changes decisions, and explicitly authorized reviewer or assignee mutations. Also use when explicitly invoked for another GitHub repository.
---

# Synventis GitHub PR Review

Perform an evidence-led review against the actual change contract and operating model. Own every
finding and verdict; never relay another agent's, bot's, or reviewer's conclusion unchecked.

## Load the policy

Read both references before reviewing:

- [review-policy.md](references/review-policy.md) for contracts, evidence, risk, testing,
  proportionality, reassessment, and connected changes.
- [github-workflow.md](references/github-workflow.md) for complete retrieval, pinned local
  inspection, follow-up baselines, thread handling, and mutations.

Treat prior notes, memories, handoffs, and previous reports only as pointers. Reverify every
drift-prone fact live.

## 1. Establish target, lifecycle, and authorization

Resolve a GitHub URL or `owner/repository#number` exactly. Accept a bare number only when the
current repository identifies the remote unambiguously. Ask rather than guessing a namespace.

Treat an unqualified request to review as read-only. It does not authorize source edits, commits,
pushes, comments, reviews, thread resolution, Jira changes, assignments, or reviewer requests.
Drafting text authorizes drafts only. Record the exact live mutations the user authorized.

Fetch minimal PR metadata first and stop with `A draft PR is not ready for review.` when GitHub's
draft flag is set. Apply the same default stop to explicit `Draft`, `WIP`, `do-not-review`, or
equivalent title/label markers, but allow the prompt to override only those informal markers. Stop
pending mutations if the PR closes or merges.

## 2. Retrieve a complete live snapshot

Run the bundled read-only collector as the canonical GitHub completeness check:

```bash
python3 <skill-directory>/scripts/fetch_pr_context.py OWNER/REPOSITORY#NUMBER
```

The collector requires authenticated `gh`. Do not substitute `gh pr view --comments`, a connector,
or an unpaginated API call. A connector may corroborate or augment the snapshot. If any required
GitHub collection is incomplete, inspect provisionally but withhold the verdict and every mutation.

Fetch each linked Jira issue live with the best authenticated Jira capability available. Include
the authoritative fields, acceptance criteria, material comments, and relevant linked issues. If
Jira is unavailable or incomplete, inspect provisionally but withhold the contract verdict,
approval, request changes, and all mutations. Do not invent a Jira requirement when no issue exists.

Read repository instructions, the PR body, relevant README and design or operations documentation,
changed code, surrounding implementation, tests, and established local patterns. Pin the exact
base and head SHAs. Use local Git for the authoritative diff because API patches may be truncated.
Protect the user's checkout as directed in [github-workflow.md](references/github-workflow.md).

For multiple connected PRs, pin every repository independently and also build one shared
requirement-to-PR coverage map. Validate interfaces, version or source pins, dependency and merge
order, integration coverage, rollout assumptions, and every intermediate deployment state.

## 3. Build the review contract

Determine and state:

- the authoritative requirements and unresolved conflicts;
- the maturity lens: automated production path, supported operational tooling, manual or
  best-effort helper, experimental or initial-research foundation, or an evidenced mixture;
- the actual deployment, threat, cardinality, source-of-truth, and accepted-risk model;
- whether the change is a bug or regression fix and therefore subject to the mandatory test gate.

Repository and organization safety or coding policies remain binding. Do not silently choose
between conflicting Jira acceptance criteria and PR scope. Withhold the verdict until the
responsible owner resolves a material conflict.

For a bug or regression fix, require the authoritative Jira acceptance criteria to name the
automated regression-test requirement. With no Jira, require it in the explicit PR contract. If it
is absent, report an incomplete contract under `Contract blockers` and withhold the verdict. Apply
the exception process in [review-policy.md](references/review-policy.md); never invent a waiver.

## 4. Inspect and validate candidates

Review the pinned `base...head` diff and the affected execution paths. Run the smallest safe
validation set capable of verifying changed behavior. Scale validation to the actual risk and
operating model without weakening explicit contract requirements.

For every candidate, independently verify all of the following before calling it a finding:

1. The factual and runtime or tool-semantics claim is correct.
2. The PR introduces, worsens, exposes, or newly depends on the problem.
3. A concrete plausible failure exists in the actual operating model.
4. Impact and likelihood justify the risk label.
5. The behavior violates the understood contract.
6. The proposed outcome belongs in this PR.
7. A smallest viable behavioral remedy exists.

Keep unverified concerns in `Questions` or `Validation limitations`, never in `Findings`. Exclude
style-only, speculative, pre-existing, and automatically enforced lint or CI observations. Treat
bot, scanner, AI, subagent, and other-reviewer output as candidates only. If separately authorized
subagents are used, independently validate, deduplicate, classify, and own their candidates.

## 5. Reset after material pushback

Whenever an author, maintainer, issue owner, or responsible operator disputes a finding or supplies
material scope, design, threat-model, architectural, or operational context, stop defending the old
finding and perform this visible reset:

1. Extract the new factual claims, intended contract, constraints, authority, and accepted risks.
2. Verify every cheaply checkable claim against live code, Jira, repository context, dependencies,
   or operations documentation. Attribute unverifiable operational evidence.
3. Restate the updated contract neutrally and surface any unresolved authority conflict.
4. Reassess the finding from scratch for fact, PR introduction, contract violation, scenario,
   impact, likelihood, remedy, scope, and merge effect.
5. Reassess every adjacent finding that depended on the changed assumption.
6. Record what changed and classify the result as `upheld`, `reframed`, `downgraded`, `converted`,
   `addressed`, or `withdrawn`.

When reassessment invalidates or weakens a posted claim, explicitly correct the thread when that
reply is authorized; silent resolution is insufficient for a materially wrong claim or severity.

After a second substantive disagreement following one completed and explained reset, stop further
AI-generated argument when only design preference, value judgment, or accepted-risk ownership
remains. Propose a short direct human conversation and later record only its technical outcome.
Preserve any independently verified blocker.

## 6. Decide and report

Before the final read-only verdict, refetch GitHub conversation and Jira contract state. If the
effective diff or material context changed, reassess it. If state keeps changing or completeness
cannot be re-established, return a SHA-pinned provisional snapshot and withhold the verdict.

Lead with an auditable header containing repository and PR, base and head SHAs, Jira contract or
`none`, maturity, review baseline or delta, and recommended verdict. Then report only:

1. `Contract blockers`, if any.
2. Verified `Findings`, each using the schema in
   [review-policy.md](references/review-policy.md).
3. Material `Questions` and unknown external context.
4. Validation performed and blocked.
5. For connected changes, per-PR verdicts plus one overall completeness verdict.

Omit generic praise, style narration, and checklist recitals. If no findings survive, say so.

Map the recommendation to GitHub as follows:

- `REQUEST_CHANGES`: at least one verified current-PR blocker.
- `APPROVE`: the contract is met with no blocker or material uncertainty.
- `COMMENT`: the review is provisional, contract verification is blocked, or material questions
  remain without a verified blocker.

Never approve conditionally while listing required pre-merge work. Allow clearly non-blocking open
questions or suggestions, but not stale findings, unprocessed disputes, or unmet blockers.

## 7. Mutate only when authorized

Follow [github-workflow.md](references/github-workflow.md) exactly. Refetch the PR, Jira, checks,
effective diff, pending reviews, and thread state immediately before mutation. A changed head,
effective base, contract, or material context invalidates prior authorization; reassess and obtain
renewed authorization.

Default to presenting exact proposed comments, replies, resolutions, review event, assignee changes,
and reviewer changes before executing. Treat reply and resolution as separate mutations. Batch
validated initial inline findings into one GitHub review; use existing threads for follow-up replies.
After every mutation set, read back and report exact final state.
