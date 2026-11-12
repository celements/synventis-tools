# Behavior classification scenarios

Use these fixtures to evaluate review decisions against the skill and its references. These are
behavioral evaluation cases, not executable collector tests. For each case, draft the initial
finding comment and the follow-up assessment after correction. Check the classification, baseline
evidence, testing consequence, and verdict against the expected outcome. Assume complete context
and no unrelated blockers unless specified. A possible approval remains subject to the other gates.

## New helper corrected during development

Input: An unmerged PR introduces an opt-in setup helper that does not exist in the base. A review
finds that its new temporary-file name is wrong. The author fixes it. The reviewer executes focused
setup and restore checks successfully. No established behavior is affected and no issue or policy
requires a retained test for this scenario.

Expected: `Correcting new behavior`. The initial finding explains that the helper is new and names
the focused verification. Do not require a new retained regression test, an acceptance-criteria
amendment, or a human test-gap override solely because the finding was fixed. After correction,
approval may be recommended. Report executed checks separately from retained coverage.

## Jira Bug for new functionality

Input: The same new-helper defect is tracked as a Jira `Bug`. The contract requires correct setup
and restore behavior but specifies no automated test. Base inspection confirms the helper is new.

Expected: `Correcting new behavior`. The issue type alone does not trigger the mandatory rule or
make the contract incomplete. Assess the actual contract and verification as in the preceding case.

## Longstanding defect that never worked

Input: A supported importer has always discarded quoted fields incorrectly. A PR repairs that
failure. Its linked issue requires correct quoted-field handling but omits regression coverage.

Expected: `Repairing an established defect`. Cite the supported baseline in the initial finding or
test-gap comment and name the quoted-field failure scenario. The mandatory rule applies even though
the importer never handled it correctly. Surface the missing test acceptance criterion and withhold
the skill's approval recommendation until the contract or its valid exception resolves the gap.

## Regression caught before first merge

Input: A new export option changes shared parsing and breaks an existing supported import format.
The reviewer reproduces the failure on the PR head and success on the base. The author fixes it
before merge, but only a one-time reproduction covers the scenario.

Expected: `Preventing a regression in established behavior`. The initial comment identifies the
existing format, base/head evidence, and mandatory retained coverage. An unmerged branch does not
remove the requirement. A one-time check alone does not satisfy it without the valid exception.

## Existing test already covers the failure

Input: In the preceding regression case, an existing automated test explicitly exercises the
affected format. It fails on the broken revision and passes on the corrected head. The authoritative
acceptance criteria already name the regression requirement.

Expected: `Preventing a regression in established behavior`. Retained coverage satisfies the rule;
do not demand a new test file or duplicate test. Approval may follow correction and verification.

## Explicit test requirement for new behavior

Input: A new feature has an edge-case defect, and its issue explicitly requires an automated test
for that edge case. The code is corrected and a manual check passes, but the required test is absent.

Expected: `Correcting new behavior`. The blanket regression rule does not apply, but the explicit
contract requirement remains unmet. Cite that requirement in the initial finding. Manual evidence
and the new-behavior classification do not waive it or justify approval.

## High-risk new behavior

Input: A first-time bulk-delete feature can delete another tenant's records because it omits a
tenant predicate. The author adds the predicate. Only a single-tenant manual check has been run;
there is no retained cross-tenant isolation coverage or explicit test acceptance criterion.

Expected: `Correcting new behavior`. Explain the concrete data-loss and isolation scenario and why
the single-tenant check cannot verify it. Require suitable verification and justify any retained
automated test request from the actual risk. Do not automatically invoke the established-defect
contract-amendment gate or approve merely because the feature is new.

## Mixed change and changed evidence

Input: A PR adds a new formatter and changes an existing serialization path. The initial finding
concerns only the new formatter. Later base/head reproduction establishes that the shared path also
breaks an existing supported format.

Expected: Initially classify the formatter defect as `Correcting new behavior`. Reassess the newly
evidenced compatibility failure as `Preventing a regression in established behavior`, explain the
new baseline evidence and resulting mandatory test requirement, and reconsider dependent findings.
Do not apply one classification indiscriminately to the whole PR or quietly add a gate after a fix.
