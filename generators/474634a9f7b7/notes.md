# Working notes: 474634a9f7b7

## 2026-10-07 review-08b31cd0c991a0a1

Lead used: prior return `local-random-ddd7dd665c4e`, especially its retained
`bounded_shape_templates`, `selected_authority_sync`, and
`top_right_only_shortcut` notes.  Those notes were treated as hypotheses rather
than current measurements.

Baseline battery reproduced a source-authority defect: both active
`racket_target.target_code` copies were behaviorally equivalent to, but not
text-identical with, the canonical `program_solution`.  The selected copies are
now byte-for-byte canonical while their archival `raw_code` fields remain
unchanged.

The generator keeps the established four-slot cardinal curriculum and adds an
independently constructed `branched` component family alongside the original
`layered` family.  `shape_family` is an exact observable override; the default
sampler draws both families.  The canonical rule and its pinned normalized hash
remain unchanged.  Task-local tests were written to fail on the missing family
contract before implementation, then extended across every declared joint
override combination.

`workspace/probe_shape_families.py` is a reusable finite diagnostic for family
support, cyclic query rotations, current declared rivals, and the canonical-
fitting `top_or_right_only` counterexample.  It is not a substitute for the
Racket authority checks or a proof against undeclared rules.
## Current reviewer considerations

Source SHA-256: `c7fe013a02193d62b60dcbd37a2bc4d713bb763721382e3dcdb78b61892d92c1`.

# Decisions for review-c7bae2b358dacd6d

## D1 — Validate exact public request types at one boundary

**Decision.** Add `_validate_request` and call it immediately after unknown-key
rejection. Require exact `int` for `seed`, nonnegative exact `int` for
`sample_index`, exact allowed `str` or `None` for difficulty, exact `int` for
integer axes, and exact `str` for enum axes.

**Why.** The baseline accepted coercible values that collapsed distinct API
requests onto one generated draw. Central validation fixes the source of the
problem and keeps lower-level draw helpers simple.

**Rejected alternatives.** Replacing scattered `int(...)` calls would leave
booleans and other aliases at other boundaries. Depending only on `gen_ctx`
would not guarantee strict scalar semantics for all public parameters. Silent
normalization was rejected because the axis contract promises exact controls.

**Evidence and limits.** The red snapshot is under
`checks/tdd-red-canonical/`; final focused tests and the full override/defect
gates are green. This deliberately changes only invalid-input behavior.

## D2 — Do not bump v4.1.0 or the rule hash

**Decision.** Keep `VERSION = "4.1.0"` and `RULE_HASH = "36dadf3bcc6b"`.

**Why.** Valid request outputs, sampling, canonical labels, and selected Racket
text are byte-for-byte unchanged. The repair tightens rejected inputs and fixes
rival metadata only; treating it as a new generative/rule version would imply a
behavioral change that did not occur.

**Rejected alternative.** A patch version bump was considered but would create
an unnecessary approval/hash churn without a changed valid-output distribution.

## D3 — Declare only the actual canonical-fitting shortcut

**Decision.** Set `CANONICAL_SHORTCUTS` to the single
`top_or_right_only` callable. Keep all named alternatives in
`SEMANTIC_RIVALS`/`LESSON_COMPETITORS`.

**Why.** Eight canonical pairs support `top_or_right_only`; the other named
rivals are already refuted by canonical evidence. The two concepts have
different purposes: one records hypotheses invisible on canonical examples,
the other challenges generated lessons.

**Rejected alternative.** Removing canonical-shortcut metadata entirely would
hide a real dataset bias. Leaving all rivals declared would continue producing
false contract failures and misleading reports.

## D4 — Preserve the existing four-demo curriculum

**Decision.** Retain four ordered demonstrations and the next generated pair as
query. Keep the top/right/bottom/left period-four schedule, then verify every
held-out position rather than redesigning the sampler.

**Why.** The current schedule already gives every production window all four
answer-bearing sectors. The 300-lesson Racket census and all 1,500 rotations
refute every declared rival, including the canonical-fitting shortcut.

**Rejected alternatives.** Random target sides can omit bottom or left and
resurrect `top_or_right_only`. More demonstrations add cost without addressing a
measured failure. Changing geometry and curriculum simultaneously would make the
repair harder to attribute.

**Limit.** This is finite-rival evidence, not a proof against undeclared rules.

## D5 — Keep the inherited test frozen; add separate regressions

**Decision.** Restore `tests/test_generator_474634a9f7b7.py` byte-for-byte and
place new tests in `test_contract_repairs.py` and
`test_parametric_bar_length.py`.

**Why.** The inherited file is part of prior accepted evidence. Separate files
make the new contract and prototype scope explicit while preserving historical
hash identity.

**Rejected alternative.** Appending tests to the inherited file would work
functionally but destroy the frozen comparison signal.

## D6 — Prototype bar length outside production

**Decision.** Implement a task-local parametric prototype with
`bar_length ∈ {1,3}`, selected once per episode. Keep setting 3 as the exact
canonical program and setting 1 as a centered one-cell marker.

**Why.** Marker length is a small semantic change that preserves the task's
object identification, orientation, erasure, and opposite-edge reasoning. The
demonstrations can distinguish the settings directly.

**Rejected alternatives.** Varying object count, grid size, shape family, or
sampling weights changes inputs but not the executed transformation. Varying
target side or color would entangle the parameter with already-required
invariances. Wiring the parameter into production was rejected because the
packet explicitly provides no production parametric-rule API.

**Evidence and limits.** Four complete episodes cover both settings and refute
the opposite setting, with labels produced only by executed Racket. Only values
1 and 3 and seeds 0/17 are studied. The prototype is proposed, not approved.

## D7 — Refresh the shortcut witness against final bytes

**Decision.** Regenerate the `top_or_right_only` counterexample on the final
selected source and retain both the task-local source-bound record and public
Racket apply receipt.

**Why.** The inherited witness was semantically useful but bound to a previous
generator hash. A final-source witness eliminates ambiguity about which bytes
produced the generated bottom target.

**Rejected alternative.** Merely referencing the prior witness would leave the
maintainer to infer source equivalence.

## D8 — Audit adversarially but do not repair audit targets

**Decision.** Reproduce concrete defects for both assigned audit-only targets,
execute public Racket where needed, and leave their sources unchanged.

**Why.** The assignment limits patch scope to `474634a9f7b7`. Exact witnesses
are more useful than speculative edits outside that scope.

**Findings.** `bd5721e5e728` ignores declared controls and lacks a semantic
contract/tests. `d40a839c7d8b` has a portable-test path defect and two
unidentifiable three-demo lessons. See `AUDIT.md` and `checks/audit/`.

## D9 — Preserve compact summaries and compress only bulky raw census reports

**Decision.** Keep each 12-KiB source-bound census companion JSON directly
readable and retain each multi-megabyte full report as a deterministic
compressed artifact with original SHA-256/byte count and decompression commands.

**Why.** The return has a 25-MiB expanded evidence budget. Compression preserves
all raw rows without deleting the only source-bound evidence, while keeping the
one-minute maintainer path in the compact summaries.

**Rejected alternative.** Dropping raw reports would make exceptional replay
harder; returning three uncompressed reports would exceed the package budget.
