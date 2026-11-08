# Working notes: 80271cb9b303

## Review `review-f1933f51f5620f1b`

### Reproduced defect

Version `3.0.0` declared a default period curriculum of `4, 3, then 5..6`, but
slot 2 called the unrestricted `3..6` draw. Across seeds `0..63` and four
difficulty settings, 112 of 256 slot-2 draws violated the declaration: each
band produced period histogram `{3: 14, 4: 14, 5: 20, 6: 16}`. The ordinary
single-sample, semantic-witness, lesson-identifiability, and override gates all
passed because slots 0 and 1 already refuted the fixed-period rivals; none
checked the declared sequence-level curriculum itself. Evidence:
`checks/before-curriculum-contract.json`.

### Repair

* Bumped `VERSION` to `3.1.0` because the default distribution changed.
* Kept explicit period overrides valid over the full advertised range `3..6`.
* Made the three default branches explicit: slot 0 -> `4`, slot 1 -> `3`, slot
  2 -> keyed random draw over `5..6`.
* Added `tests/test_curriculum_schedule.py`; it failed against the original
  source in all four difficulty modes and passes against `3.1.0`.
* Added `workspace/curriculum_probe.py` and documented its source-bound command.

The final 200-seed-per-band probe generated 3,600 grids and assembled 1,800
three-demo lesson windows over all cyclic starts. It found zero period-contract,
`self_check`, lesson-identifiability, or harmful-rival-survival failures. Each
band had 1,198 unique inputs among 1,200 generated grids and slot-2 histogram
`{5: 92, 6: 108}`. Evidence: `checks/after-curriculum-probe.json`.

### Authority synchronization

The canonical program and selected solution's `raw_code`/`target_code` were
whitespace-normalized equivalents but differed in exact formatting. The first
`authority_sync` run therefore failed even though execution parity passed.
Both selected fields were replaced with the exact canonical program text. The
normalized rule hash remains `4cb32d01d908`, canonical outputs are unchanged,
and the repaired authority-sync stage passes. This is a source-text
synchronization, not a semantic rule rewrite.

### Deliberately unchanged

* The canonical ledger and Racket semantics were not changed.
* The baseline frozen `tests/test_generator_80271cb9b303.py` was restored
  byte-for-byte to its assignment SHA-256
  `379cd4c624b779de00a9045629f93ed47a17ef349608521117639ac69d45f841`.
* Other axes and rivals were left unchanged after their existing validators,
  exact overrides, Racket smoke tests, and the larger task-local probe passed.

### Limits

The finite curriculum probe is strong regression evidence, not a universal
induction proof. It uses the Python parity solver for sequence-level checks;
Racket execution remains covered separately by rule-smoke and authority stages.
## Current reviewer considerations

Source SHA-256: `d8478c24edec8ac12b472518bc49448a0730943fd5a26e279e5f27e38a741c34`.

# Decisions — review-f1933f51f5620f1b

## G1 — Enforce the declared three-slot period curriculum

**Observed state.** Version `3.0.0` documented slot periods `4`, `3`, and
`5..6`, but implemented the third slot as an unrestricted `3..6` draw. The
original rationale is recoverable from the module comments and rival set: the
first two slots anchor canonical periods 4 and 3, while the third should expose
a genuinely longer period so a three-example lesson spans qualitatively
different periodicities.

**Decision.** Keep slots 0 and 1 fixed at 4 and 3. Restrict the unoverridden
slot-2 keyed draw to 5 or 6. This is the smallest change that makes generated
behavior match the existing contract.

**Rejected alternatives.** Updating the prose to say `3..6` would preserve the
bug rather than the intended curriculum and would allow a lesson cycle with no
long period. Fixing slot 2 to only 5 or only 6 would satisfy the broad idea but
unnecessarily remove diversity. Reordering slots would change lesson assembly
without evidence of benefit.

**Probe and failure mode.** The original source failed 112/256 slot-2 checks
across seeds `0..63` and four difficulty settings. The final 200-seed-per-band
probe observed `{5: 92, 6: 108}` in slot 2 for every band and no contract
failure. A future regression could still preserve marginal 5/6 support while
breaking a cyclic lesson; therefore the retained probe tests all cyclic starts,
not only per-slot histograms.

## G1 — Preserve explicit override support over periods 3..6

**Decision.** Default scheduling and explicit controls are separate branches.
An explicit `period` override still passes through the original `3..6`
validation, including period 3 or 4 in slot 2.

**Reason.** `AXES["period"]["valid"]` promises exact control over all four
periods. Narrowing override support to the default slot range would repair one
contract by breaking another. The final override battery accepted 68,220 of
68,220 draws over 758 cases and three bands.

## G1 — Bump the generator version to 3.1.0

**Decision.** The default output distribution changed, so `VERSION` moved from
`3.0.0` to `3.1.0` rather than silently changing keyed draws under the old cache
identity.

**Consequence.** Non-fixed random choices can change because version is part of
the keyed RNG salt. This is intentional cache invalidation. Semantic axes,
valid ranges, and the rule remain unchanged.

## G2 — Synchronize active Racket authority text exactly

**Observed state.** The canonical program and selected solution
`raw_code`/`target_code` had identical whitespace-normalized forms and execution
parity, but different formatting. The strict authority stage therefore failed.

**Decision.** Copy the exact canonical program string into both selected
solution fields. Do not alter the canonical ledger or the program's normalized
form. The normalized rule hash remains `4cb32d01d908` and execution parity now
runs over one exact source group.

**Rejected alternative.** Weakening `authority_sync` to accept normalized
agreement would leave multiple active byte authorities and make future source
identity ambiguous. A semantic rule rewrite was unnecessary and riskier.

## T1 — Add a task-local regression test without editing the frozen fixture

**Decision.** Add `tests/test_curriculum_schedule.py` as a source-bound test.
The assignment's existing `test_generator_80271cb9b303.py` is a frozen fixture
and was restored to its exact baseline SHA-256 after an exploratory attempt to
run it directly exposed its runtime-layout dependency.

The new test checks all four difficulty settings over 64 seeds, requires slots
0/1/2 to be `4`, `3`, and `5|6`, and requires both long periods to occur. It was
observed red before the generator change and is green afterward.

## T1 — Retain a reusable sequence-level probe

**Decision.** Add `workspace/curriculum_probe.py` rather than leave a one-off
notebook or prose claim. The probe source-loads the selected generator, reads
its actual `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS`, checks 200 seeds per
band by default, assembles every cyclic lesson start, records exact hashes and
denominators, and exits nonzero on contract, validation, identifiability, or
harmful-rival failures.

**Boundary.** The probe uses the Python parity solver and does not replace
Racket rule-smoke or authority synchronization. Its finite sample does not
establish universal induction.

## Existing distribution choices left unchanged

The other three-slot choices remain as found: cutoff styles
`mixed/partial/aligned`, leading-zero styles
`mixed/all_zero/all_nonzero`, a canonical-scale bottom block in slot 0, and
keyed variation in layout, palette, dimensions, and row count elsewhere. Their
precise historical rationale is not documented beyond comments, but the
combination fires all seven declared semantic witnesses, accepts all four
canonical pairs, and produced zero harmful competitor survivals in the larger
probe. Broad refactoring was rejected because it would expand scope without a
reproduced defect.

## Audit-only decisions

Findings A1 (`5b40e03f0a23`) and A2 (`5d15679fbc44`) are documented in
`AUDIT.md` with reproducible evidence. Per assignment, neither audit target was
modified. Their proposed fixes would require separate task ownership and fresh
before/after qualification.

## Review `review-a0b13fb270e8873e` — semantic declaration repair

### Reproduced defect

The selected `3.1.0` generator correctly taught the periodic extension rule,
but it copied all seven `SEMANTIC_RIVALS` into `CANONICAL_SHORTCUTS`. A
source-bound replay over the four labeled canonical pairs showed that none of
the seven rivals fits all four; their per-pair match vectors are retained in
`checks/root-cause-before/80271cb9b303-invalid-shortcuts.json`. The shared
semantic gate therefore rejected the declaration before checking generated
counterexamples.

### Repair and decision

`LESSON_COMPETITORS` remains the full rival set because the generated lessons
must still refute those plausible mistakes. `CANONICAL_SHORTCUTS` is now empty,
which states the narrower fact actually supported by the canonical data. A new
source-bound regression test computes canonical fit from the live rival
functions and requires the declaration to equal that computed subset.

`VERSION` remains `3.1.0`: this edit changes diagnostic metadata only. It does
not alter keyed generation, axes, examples, the Python solver, or the Racket
authority. The repaired source SHA-256 is
`174ca5baed3dbde7440f328eef878698ce4ca98b9424621bff29c5f6f77abe76`;
the normalized rule hash remains `4cb32d01d908`.

### Verification and limit

The new semantic-declaration tests and the retained curriculum tests pass
(6 tests total), and the post-repair semantic gate accepts 4/4 canonical pairs,
fires and verifies all seven witness/rival claims, and identifies 12/12 sampled
lessons. The packet's aggregate `task_tests` wrapper still stops before pytest
because the immutable issued `test_generator_80271cb9b303.py` guesses a
repository-relative canonical path. That frozen fixture was not edited; the
portable added tests and semantic gate were run separately and are retained as
evidence.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d375f053896bbf58:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d8478c24edec8ac12b472518bc49448a0730943fd5a26e279e5f27e38a741c34`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

The retained audit explicitly reported no issue in its bounded source-bound scope. Preserve that limitation; no universal correctness or new owner execution is inferred.

### Assessment or prior finding

## 80271cb9b303

**No issue found** in the checked domain. Generator SHA-256
`d8478c24edec8ac12b472518bc49448a0730943fd5a26e279e5f27e38a741c34`
was checked for the declared `4,3,5..6` period curriculum, exact slot behavior,
self-check validity, all three cyclic lesson starts, declared competitor
survival, and canonical-shortcut fit. Four schedule regression tests passed.
A fresh task-local probe generated 900 grids across easy/medium/hard, all 900
were unique within the summed per-band counts, and 450 cyclic lesson windows had
zero period-contract failures, self-check failures, lesson-identifiability
failures, or harmful competitor survivals.

Evidence: `checks/audit/80271cb9b303/task-tests.log` and
`checks/audit/80271cb9b303/curriculum-probe.json`. This is finite coverage of the
declared rivals, not a proof that no undeclared periodic-extension shortcut
exists. I left the target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d375f053896bbf58-v0001/audit_assets.json), manifest SHA-256 `4d7ca2dff9ed9e5e0c88bc5889256141094e3ee9b98a9710b5509b18976f8922`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Native parametric return — 2026-10-24, review-d343b7f87571f4dc

Production remains version `3.1.0`, SHA-256
`174ca5baed3dbde7440f328eef878698ce4ca98b9424621bff29c5f6f77abe76`.
The new task-local prototype is `workspace/parametric/native_family.py`, with
its exact-path adapter, input-only sampler, protected audit and promotion
contract. `continuation=repeat` returns the exact canonical program, SHA-256
`7278144d22eaa349ae7e24bf6ab2f771d19577b1f1fa66513c54d79861440c22`;
the normalized authority hash remains `4cb32d01d908`.

### New rule family and dependency

Infer each nonempty row's smallest period through its inclusive rightmost
nonzero column R, preserving leading/internal zeros as observations. The
intermediate is `(period, motif, R mod period)`. Preserve the observed prefix
and continue by `repeat`, `reverse_cycle`, or `bounce`. Reverse moves backward
around the primitive motif. Bounce moves forward from the observed phase and
reflects without repeating either endpoint. Both wrap/turn locations depend
on the inferred period, so the traversal cannot be chosen before inference.

The separate prototype accepts all strict rectangular integer grids up to
30×30, including blank rows, a nonzero at R=0, period one, observations without
a repeated residue, full-width rows and mixed row periods. This is a natural
extension of the narrower production sampling grammar. Periods one and two
give identical behavior under all three settings; larger asymmetric motifs
provide the teaching evidence. Original production and canonical code were
not changed.

Constructive three-demo inputs expose periods 1–8, partial/aligned cutoffs,
leading/trailing motif zeros and long tails passing reflection turns. Inputs
are matched across settings, with independent counts of 3–6 demos and 1–4
queries. Full six-plus-four banks precede slicing. Queries range from 1×9 to
30×30; the dense stress cases have 28 active rows and 523/515 occupied input
cells for seeds 0/17, extending through column 23 before blank continuation.

### Executed checks and corrections

- **77 focused tests passed:** 63 adapter and 14 audit tests. Independent
  literals cover all policies, period/phase edge cases and public projection;
  the audit tests include negative export/verifier cases.
- The initial alternate rule had a missing final delimiter. The wrapper
  rejected it before alternate Racket execution; after correction, the focused
  26-test semantics selection and full 77-test suite passed. The reused audit's
  five-pair guard was separately changed to this task's four after a red test.
- **Protected teaching audit passed:** four canonical pairs, 42 generated
  labels, 182/182 candidate comparisons refuted by the first three demos,
  zero survivors/failures, 532 uncached evaluations and 24 strict public files.
  Coverage includes both seeds and all three settings, with colors 1–9.
- **Native qualification passed:** six jobs, three demos/four queries and
  78 protected evaluations. Inventory is
  `workspace/parametric/evidence/manifest.json`; qualification and execution
  are retained in `checks/80271cb9b303/qualification/` in the return.
- **Causal replay passed:** in the two seed-0 first-demo cases, replacing only
  minimum-period selection with observed-prefix length changes 26 output cells
  for reverse-cycle and 28 for bounce. Inputs, rightmost delimiters, preserved
  prefixes and traversal code remain fixed. Programs, intermediate values and
  labels are retained in `checks/80271cb9b303/causal/`.

The reusable audit checks finite executable rivals on demonstrations, never
counting execution errors as refutations. Its public exporter/verifier binds
exact visible bytes and exposes only one query input; programs, settings,
answers, future queries and turn-count hints remain private.

Status is reviewer **ready**, with no unresolved check failure in this new
prototype. The retained historical audit applies only to its stated older
source; its disposition was not reinterpreted. Historical production batteries
and the frozen fixture were not rerun or edited. All current claims are bounded
regression/rival evidence, not universal identifiability. Next action: integrate
the exact returned source and run owner qualification/acceptance. Owner
acceptance and training admission were not performed here.
