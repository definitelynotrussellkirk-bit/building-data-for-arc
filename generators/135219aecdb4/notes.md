# Working notes: 135219aecdb4

## 2026-10-02 review — assignment review-590099c9bdb33930

### Baseline

- Source-bound battery: 11/12 green.
- Only failing gate: exact selected-authority synchronization. Canonical and selected target executed identically but differed in bytes; archival raw source also differed.
- Generator v2.0.0 advertised three passes but its `cascade` profile accepted either 2 or 3 and had no two-pass rival.

### Root-cause probe

`workspace/mask_space_census.py` exactly enumerates erasure masks. Key counts of true three-pass masks:

- base 0: n=5 → 0, n=6 → 0, n=7 → 192
- base 1: n=5 → 32, n=6 → 416, n=7 → 2,096

Choosing a base before checking profile feasibility caused ordinary cascade slots to fall back when the selected class had no valid chain. Five-hole true-three-pass masks necessarily erase only two symbol values, so symbol breadth must be supplied elsewhere in the lesson.

### Implemented

- v2.1.0 profile schedule: `one_pass`, `three_pass_cascade`, `joint_constraints`.
- Feasible `(base, masks)` selection across both classes.
- `two_pass_only` rival and exact three-pass witness.
- Lesson identifiability now explicitly refutes a two-pass solver.
- Exact canonical source copied into selected `target_code`; `raw_code` kept archival.
- Regression test covers cascade slots across all bands.

### Verification

- After battery: 12/12 green.
- Semantic gate: 600/600 strict, 4/4 witnesses, 4/4 rival claims, 12/12 lessons identifiable.
- Override gate: 990/990 accepted.
- Focused pytest: 11 passed.
- Census tool test: 1 passed.

### Known limits

- Explicit counts that cannot support their scheduled witness preserve the count and use a lawful fallback.
- Easy five-hole cascades carry only two missing symbols; lesson-level peers provide broader symbol evidence.
- Packet-wide pytest includes unavailable unrelated modules/fixtures; see root `REVIEW.md` and check logs.
## Current reviewer considerations

Source SHA-256: `e8c1e1883a69ac7a6993afd8a86f7b479aecd1cab446a164b28385450734398a`.

# Decision record — 135219aecdb4

## 1. Treat the canonical program as the active authority

- **Original state/rationale:** canonical `program_solution`, base `target_code`, and archival `raw_code` all executed correctly, but the selected target was reformatted and therefore not exact-text synchronized. Why that copy was flattened was not recorded.
- **Alternatives:** weaken the authority gate to normalized equivalence; rewrite canonical text; make archival code selected.
- **Probe:** baseline `authority_sync` and the existing exact-equality test.
- **Decision:** copy canonical `program_solution` exactly into selected `target_code`; leave `raw_code` archival.
- **Failure mode avoided:** two nominally active rule authorities can drift independently while parity happens to remain green on current examples.
- **Limitation:** archival code still differs, intentionally, and must remain explicitly non-selected.

## 2. Preserve the observable erasure-count contract

- **Original state/rationale:** `n_erased` is a declared, externally observable axis. Version 2.0.0 already fell back when a requested count could not realize the scheduled internal profile.
- **Alternatives:** reject incompatible overrides; silently change the requested count; force every override to carry every witness.
- **Probe:** 990-draw override gate and exact count assertions.
- **Decision:** keep `n_erased` exact. Search all bases for the scheduled profile first; only if none exists at that exact count, fall back to any lawful mask.
- **Failure mode avoided:** dishonest or brittle override behavior.
- **Limitation:** an explicit override can produce a sample without the ordinary schedule witness. This is deliberate and documented.

## 3. Make the full three-pass budget identifiable

- **Original state/rationale:** the `cascade` profile accepted `passes in (2, 3)`, sufficient to refute a one-pass rival but not a two-pass rival.
- **Alternatives:** keep a generic multi-pass concept; change the canonical rule to two passes; increase demo count without a semantic contract.
- **Probe:** exact mask census plus a failing regression across all three difficulty bands.
- **Decision:** require `passes_to_complete == 3`, rename the slot `three_pass_cascade`, and add `two_pass_only` to the rival set.
- **Failure mode avoided:** a model learns a two-pass approximation that fits every lesson while disagreeing with the selected rule.
- **Limitation:** pass count is taught only on ordinary scheduled lessons, not on every possible override sample.

## 4. Choose the Latin class after checking witness feasibility

- **Original state/rationale:** version 2.0.0 randomly selected a base first, then searched masks only within that class. This was simple but assumed profile availability was uniform.
- **Alternatives:** hard-code the cyclic base for cascade examples; retry random bases; precompute a static mask table.
- **Probe:** enumeration showed base 0 has no true three-pass mask at 5 or 6 erasures, while base 1 does.
- **Decision:** collect `(base, compatible_masks)` pairs and sample from feasible pairs.
- **Failure mode avoided:** silent fallback caused solely by choosing an incapable class first.
- **Limitation:** feasible-pair sampling is not weighted by total mask count, so base-class frequency is a curriculum choice rather than a uniform draw over all masks.

## 5. Keep symbol breadth as a lesson-level requirement

- **Original state/rationale:** the previous profile matcher required at least three missing symbols for every profile.
- **Alternatives:** require three symbols on the cascade demo; increase easy erasures; drop the symbol-breadth witness.
- **Probe:** exhaustive five-hole census proved every true three-pass chain erases only two symbol values.
- **Decision:** allow the cascade demo to use two missing values while requiring the lesson to contain another demo with at least three missing values.
- **Failure mode avoided:** making the easy three-pass slot impossible or falsely claiming it exists.
- **Limitation:** a single cascade example viewed out of lesson context has weaker palette evidence.

## 6. Do not alter the Racket rule semantics

- **Original state/rationale:** rule smoke, parity, canonical examples, and the Python mirror all agreed; the defect was teaching distribution and source provenance, not execution.
- **Alternatives:** simplify the rule, iterate to a fixed point, or change the pass count.
- **Probe:** 40-seed parity, canonical pairs, authority execution parity, and after rule smoke.
- **Decision:** leave canonical Racket semantics unchanged.
- **Failure mode avoided:** “fixing” correct task semantics to match a shortcut in the generator.
- **Limitation:** bounded three-pass behavior can differ from fixed-point completion on deeper chains; that distinction is now intentionally taught.

## 7. Add a reusable exact census rather than rely on seed anecdotes

- **Original state/rationale:** existing gates sample many seeds but did not answer why witness availability differed by base and erasure count.
- **Alternatives:** ad hoc notebook; hard-coded counts in comments; larger random sample.
- **Probe:** test-first workspace utility, then exact enumeration.
- **Decision:** add `workspace/mask_space_census.py`, a focused regression test, and JSON output for counts 5–7.
- **Failure mode avoided:** future reviewers reintroduce impossible profile constraints or misdiagnose random fallback.
- **Limitation:** the tool uses selected generator internals and is task-specific, not a general ARC census framework.

## 8. Stop after the smallest supported change

- **Original state/rationale:** all correctness and distribution gates except authority sync were already green.
- **Alternatives:** redesign the generator, add more Latin classes, widen grid sizes, or rewrite shared tooling.
- **Probe:** after battery, focused tests, exact census, and visible solve.
- **Decision:** limit source changes to the selected generator, its tests/summary/workspace, and the selected base authority.
- **Failure mode avoided:** unrelated refactoring obscures causality and expands review risk.
- **Limitation:** broader packet test-export problems remain documented rather than repaired because shared-source edits are outside the assignment scope.

## 2026-10-23 review — assignment review-cdba55facdaf4771

### Exact override repair

- Baseline `generator.py` SHA-256 was `e8c1e1883a69ac7a6993afd8a86f7b479aecd1cab446a164b28385450734398a` at v2.1.0.
- The retained audit defect reproduced: explicit `n_erased=True`, `1.9`, and `"3"` were silently coerced instead of rejected.
- v2.1.1 now rejects any explicit non-exact integer before `gen_ctx`; current generator SHA-256 is `9fe9fb320bc4b64d8fa1a0b353311c9eeb322c1514d2c8a7160b2a6055ec5992`.
- Canonical Racket semantics, canonical text, selected authority, and `RULE_HASH=8036db043882` are unchanged.

### Proposed episode-level pass budget

- Added a task-local prototype with `pass_count ∈ {1,2,3}`, default `3`, selected once per episode. The three-pass program is byte-for-byte canonical; alternatives change only nested `fill` depth.
- Demonstration and query counts are independent. Retained seed-17 evidence uses two demonstrations and four distinct queries for each setting over six shared lawful true-three-pass inputs.
- Every retained label was executed by protected Racket, agrees with the independent Python mirror, and every demonstration and query separates the selected setting from both alternatives.
- Public challenge names hash exactly the visible bytes; query answers, settings, seeds, programs, and source metadata remain private.
- The sampler now bounds actual generator draws. The evidence writer rejects single-setting runs, missing-default runs, duplicate settings, nonempty destinations, and program-file/hash mismatches.
- This extension remains `prototype_proposed_not_production_approved`; it does not change canonical selection, approval, or training admission.

### Verification and limits

- Focused production override and lint stages passed; the final task-local pytest receipt is under `checks/final-task-tests/`.
- Racket episode evidence: `checks/parametric/pass-budget-s17-v1/manifest.json`. Boundary/export attack: `checks/parametric/adversarial-max64-s29.json` (64 demos + 64 queries, 128 unique inputs).
- The optional broad audit preset completed all task tests but its semantic census was interrupted; it was not rerun because the changed production surface, prototype surface, Racket parity, and adversarial boundaries already had focused evidence.
- Evidence is bounded to the retained seeds and is not a production approval claim.

