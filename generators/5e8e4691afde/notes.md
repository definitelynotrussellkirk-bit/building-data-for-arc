# Working notes: 5e8e4691afde

## Current production decision

Reject non-exact integer `seed` and `sample_index`, and negative sample indices,
before constructing `gen_ctx`. Signed integer seeds remain valid. Keep
`VERSION = "3.0.0"`: this is an invalid-call repair, and changing the keyed RNG
version would unnecessarily change valid recipes. The canonical Racket rule
and `RULE_HASH = "ee2251228926"` are unchanged.

The retained scalar finding from `review-824e9357d6d7dadf:v0001` is repaired on
this source; its audit resolution is proposed for maintainer intake in
`checks/scalars/audit-resolution-proposal.json`. The historical evidence index
is unchanged. Its 33 invalid calls were accepted by the frozen baseline and
reject after the repair. Eight additional malformed scalar cases reject in focused
tests. The source-bound contract probe compares 136 valid recipes byte-for-byte
and executes five canonical plus 11 generated cases through Racket; all pass.
Evidence: `checks/scalars/contract-repair.json` in the reviewer return. Reproduce
with `workspace/verify_contract.py --baseline OLD_GENERATOR.py --out NEW.json`.

The task-owned tests now use `reviewer_support` to locate the selected source
and canonical/base data in either supported layout. Authority text comparison
uses the same whitespace normalization as `RULE_HASH`; compact and pretty
printing are not different rules. Frozen shared/root tests were not edited.

## Proposed parameter extension

`workspace/parametric/prototype.py` keeps the frame, indicator, path endpoint,
translated center, and diagonal output roles. Episode-fixed `quarter_turns`
in 0..3 and `distance_scale` in 1..2 act on the endpoint-minus-indicator vector.
The default (0, 1) is the exact canonical program text. The CLI supports
independent demo/query counts and defaults to four distinct queries; one query
is 30x30 and the others are 21..29 per side, larger than its 16..20 demos.

The retained seed-17 export covers all eight settings: 24 demonstrations,
32 queries, and five canonical default examples, with 61 actual Racket
program/input evaluations. All eight hypotheses are fitted using demos only;
each episode has one survivor. Public filenames hash only the visible payload.
Code, settings, seeds, query labels, and rule hashes remain in private records.

Limits: finite eight-rule identifiability, a common in-bounds layout domain,
and straight/one-bend generated paths. This is a proposed extension, not
production approval or a training-admission decision. Existing production
distribution/semantic batteries were not rerun for this scalar-only repair.

## Recovery tool proposal

`workspace/recovery/` contains a tested read-only sparse packet packager. It
uses the unchanged official builder/validator, original ZIP bytes for never
materialized immutable paths, and an extraction-time inventory that detects
deletions. It was needed because this review environment exhausted disk file
slots. The helper is task-local; promotion to shared tooling remains a separate
maintainer decision. Follow its README, especially the inventory trust boundary.

Next useful work: assess promotion of the parameter extension and recovery
helper separately from the routine scalar repair. Imported associated notes
retain their original evidence in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-824e9357d6d7dadf:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `75d65fd7c77bcc8ee14c5e007d1efb94db747cd4725216f9d00748dacffd76b8`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved on generator SHA-256 4ada1ccad8e5662a4cc0a80763d2c5400e22436b1f40a091b033fc4865b44e02: generate now rejects non-exact integer recipe scalars and negative sample indices before GenCtx. The retained 33 invalid calls reproduce on the frozen baseline and all reject after repair; eight additional scalar cases reject in focused tests. All 136 sampled valid recipes remain identical and 16 canonical/generated Racket labels match. Fresh source-bound evidence: checks/scalars/contract-repair.json; tests/test_runtime_scalars.py. Resolution is limited to this input-contract defect, with no change to the canonical rule or training admission. Exact retained source-bound capsule: `generators/5e8e4691afde/evidence/scalar-audit-resolution-e46d412157fb6873/manifest.json`. Owner did not rerun these checks; resolution is limited to this scalar-contract finding.

### Assessment or prior finding

## 5e8e4691afde

**Reproduced public-call contract defect — invalid runtime scalars are silently
accepted.** The audited v3.0.0 source SHA-256 is
`75d65fd7c77bcc8ee14c5e007d1efb94db747cd4725216f9d00748dacffd76b8`.

The direct public probe exercised 33 invalid calls across default, easy, and hard:
boolean, float, and string values for both `seed` and `sample_index`, plus
`sample_index=-1`. All 33 returned grids; none raised. The strict defect-lint stage
independently reported the same detector/count before its audit controller timeout.
This is a recipe identity/validation defect, not a demonstrated label or canonical
Racket-rule disagreement; the returned grids passed the generator's structural
self-check.

Evidence:

- `checks/audit/5e8e4691afde/strict_scalar_probe.py` — portable source-bound direct probe.
- `checks/audit/5e8e4691afde/strict-scalar-report.json` — all 33 calls, value types,
  output hashes, and self-check results.
- `checks/audit/5e8e4691afde-defect-lint/checks/5e8e4691afde_audit_defect_lint.log`
  — independent detector output (`strict-scalar: 33`).

No audit-target source was changed. A repair should reject non-exact integer
runtime scalars and negative sample indices before constructing `gen_ctx`, with
focused regressions matching the repaired assigned generator.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-824e9357d6d7dadf-v0001/audit_assets.json), manifest SHA-256 `f756d28c40995bb54de977a7c5c37583e3faa0db78544a92ce3c614fa07d0e79`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Native rotation/scale promotion — review-31996c6715efbf2f

Promote the retained eight-setting rotation/scale family through a strict native
adapter.  The default remains the exact canonical Racket bytes.  Supported
lessons use 2–6 demonstrations, exactly four distinct queries, matched inputs
across settings, and a substantive 30×30 query.  The selected setting is the
sole survivor in the bounded demonstration-only audit over all eight settings
and eight structural shortcuts for seeds 0 and 17 at 2, 3, and 6 demos.

Sequential dependency: A reads the indicator-to-extra-maroon displacement and
applies the episode transform; the intermediate is the transformed displacement
and target center; B fills the canvas and draws the relocated frame and both
diagonals through that center.  The returned protected-Racket witness ablates
that intermediate and changes the final output.  Reviewer readiness does not
constitute owner acceptance or training admission.
