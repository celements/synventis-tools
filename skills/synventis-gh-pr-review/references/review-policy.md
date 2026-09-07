# Review policy

## Contents

- [Contract authority](#contract-authority)
- [Maturity and proportionality](#maturity-and-proportionality)
- [Finding evidence and classification](#finding-evidence-and-classification)
- [Tests and CI](#tests-and-ci)
- [Operational and security evidence](#operational-and-security-evidence)
- [Connected changes](#connected-changes)
- [Documentation and follow-up work](#documentation-and-follow-up-work)
- [Reassessment output](#reassessment-output)

## Contract authority

Fetch every materially linked Jira issue. Identify the primary implementation issue from explicit PR
and commit context; treat other linked issues as dependencies or constraints. Withhold the verdict
when no primary contract can be established or their requirements conflict.

Use recorded Jira acceptance criteria as authoritative. A Jira comment changes the contract only
when it clearly comes from an authorized issue owner and leaves no conflicting recorded criteria.
An author reply may correct facts and operating assumptions, but it does not override Jira,
repository policy, security requirements, or compliance requirements. Surface a conflict instead of
silently selecting the convenient source.

Without Jira, derive the contract from the PR body, repository policy and documentation, tests, and
visible change context. Ask one focused question and withhold the verdict only when remaining
ambiguity could change compliance or expose a blocker.

Infer visible repository context instead of requiring the author to repeat it. Separate documented
facts, reasonable inferences, and unknown external or operational facts.

## Maturity and proportionality

Use one or an evidenced mixture of these lenses:

1. Automated production path.
2. Supported operational tooling.
3. Manual or best-effort helper.
4. Experimental or initial-research foundation.

Use maturity to calibrate reachability, likelihood, safeguards, testing, and documentation. It does
not excuse a verified contract violation. Do not impose an internet-facing production model on a
manual or research path without evidence.

Evaluate a consciously accepted risk as non-blocking when it conflicts with no authoritative
contract or policy and the accepting person owns the affected scope. Escalate when authority is
unclear or the decision affects other parties.

## Finding evidence and classification

Do not cap finding count. Deduplicate findings that share one root cause and smallest remedy.

Require each finding to state:

- location;
- factual status;
- concrete failure scenario and evidence;
- impact and likelihood in the actual operating model;
- derived risk;
- merge disposition and current-PR scope;
- smallest viable behavioral remedy, while allowing an equivalent implementation.

Use these factual states:

- `verified`: supported by inspected code, runtime evidence, authoritative documentation, or
  attributable operational evidence that meets the required threshold.
- `uncertain`: incomplete or conflicting evidence; keep it as a question or limitation.
- `refuted`: evidence disproves the claim; withdraw it and correct a posted record when authorized.

Derive risk from explicit impact and likelihood:

- `critical`: credible catastrophic compromise, irreversible loss, or organization-wide outage.
- `high`: substantial security, correctness, data, or operational failure in normal expected use.
- `medium`: a concrete contained failure, or serious impact with low practical likelihood.
- `low`: limited concrete impact with a plausible scenario; never style alone.

Use these labels directly. Do not translate them into `P0` through `P3` except when quoting existing
project text.

Keep merge disposition independent:

- `blocker`: a verified current-PR contract violation requiring pre-merge correction.
- `important non-blocking`: a verified concern worth recording while merge may proceed.
- `question`: an unresolved fact or contract point, not an asserted defect.
- `follow-up`: valid work outside the current PR.
- `addressed` or `withdrawn`: closed outcomes for previous findings.

Ask separately: Is it real? Does it belong in this PR? Should it block merge?

Do not report a pre-existing defect as PR-introduced unless the PR worsens, exposes, or newly depends
on it. Mention a severe pre-existing risk separately only when it materially affects safe use of the
changed path.

Report a documented coding-standard breach only when the rule is mandatory, is not enforced by
tooling, and has a concrete compatibility, maintainability, or safety consequence. Report extra
scope only when it violates a boundary or creates a concrete correctness, risk, deployment, or
reviewability problem. PR size alone is not a split threshold; request a split only when the change
cannot otherwise be reviewed reliably.

## Tests and CI

Run focused existing tests and targeted reproductions sufficient for the changed behavior. Do not
require production-scale deployment, load, or browser validation for manual or research work unless
the contract or actual risk requires it.

Report missing tests only when required by contract or repository policy, or when a concrete changed
behavior with meaningful regression risk lacks practical verification. Name the missing scenario.

Treat a change as a bug or regression fix when Jira uses the `Bug` issue type, the recorded contract
describes defective or regressed behavior, or the change clearly restores intended behavior. Ask the
responsible owner when these signals conflict.

For every bug or regression fix:

1. Require the authoritative contract to name an automated regression test as acceptance criteria.
2. Require a focused test that exercises the reported failure and would fail on the broken behavior.
3. Accept an existing test only when it explicitly covers that scenario.
4. Use the narrowest appropriate unit, integration, or end-to-end layer.
5. Where safely practical, run the test on the fixed head and against the broken behavior in an
   isolated checkout. Otherwise require credible red/green evidence and state the limitation.

Do not invent an exception. The PR author must explain why automation is impractical and record the
alternative validation strategy and rationale in the PR. With linked Jira, the responsible issue
owner must also accept the exception in the authoritative contract. Withhold the verdict while the
PR and contract conflict.

Treat CI state as evidence, not a code finding. A change-caused failure is a blocker. A verified
unrelated infrastructure failure need not prevent approval. Withhold approval when required
validation has not run and the uncertainty could hide a blocker.

## Operational and security evidence

Attribute operational claims that cannot be independently checked. A responsible operator's claim
may settle ordinary deployment-state questions. Require corroboration for high-impact safety claims,
irreversible migrations, or conflicts with the recorded source of truth.

For submodules and external repositories, inspect the exact referenced commit and verify that it is
durably reachable from the recorded source of truth. If an inaccessible dependency is necessary to
verify compliance or a potential blocker, withhold the verdict; otherwise scope the limitation.

Inspect setup and build commands before executing PR code, especially from forks. Use isolation
without unnecessary credentials or secrets. If execution cannot be made safe, use static analysis
and report the limitation.

Treat automated comments as evidence only when their contents are relevant to the reviewed contract
or changed behavior; their presence alone is not a finding.

Calibrate security findings against actual exposure, privileges, reachability, impact, and
likelihood. Do not publish active secrets, exploit details, or unnecessarily weaponizable steps in a
public PR. Put only the minimum blocking consequence there and route sensitive evidence to an
authorized private security channel.

## Connected changes

For connected multi-repository PRs, produce both per-PR verdicts and one overall readiness verdict.
Map every shared requirement to its implementing and validating PRs. Verify producer/consumer
interfaces, dependency versions, source pins, integration tests, merge order, rollout order, and
compatibility of every intermediate state.

Block an individual PR only when merging it in the planned order would itself violate the shared
contract. When a gap belongs elsewhere or has no owner, withhold the overall verdict, identify the
missing ownership, and do not mislabel the locally correct PR as defective.

## Documentation and follow-up work

Make documentation blocking only when safe or correct current-PR use depends on information that
operators or maintainers cannot recover from the changed source of truth. Otherwise route it
proportionately:

- Inline comment or nearby README: local behavior and accepted helper semantics.
- Runbook: recurring deployment, recovery, and operational procedures.
- PR or Jira: one-time rollout or migration evidence.
- ADR: durable cross-repository architectural policy and trade-offs.

Keep follow-up work separate from merge requirements. Do not assign it to the author implicitly.
Creating, editing, or assigning Jira work requires explicit authorization; otherwise provide a
draft with recommended scope and project.

## Reassessment output

For every affected thread or finding, show:

1. Prior conclusion.
2. New context, its source and authority, and verification status.
3. Updated contract.
4. Dependent findings reconsidered.
5. New result: `upheld`, `reframed`, `downgraded`, `converted`, `addressed`, or `withdrawn`.
6. Current merge effect.
7. Proposed thread action without mutation unless authorized.

Count a second informed pushback only when it is a second substantive disagreement after one full
reset was completed and explained. Multiple comments in one response are one round; repeated wording
without new reasoning is not another informed round.
