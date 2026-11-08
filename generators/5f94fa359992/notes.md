# Working notes: 5f94fa359992

## Intended rule and curriculum

Detect each hollow maroon frame and its key immediately above the frame. Tight-crop the monochrome figure inside each frame, sort crops by ascending key value, vertically center them to the tallest crop, and concatenate them with one zero column between neighbors. The generator retains five linked canonical 9×18 profiles and a four-slot schedule: one canonical anchor plus three broad profiles that refute reading-order, uncropped-interior, top-alignment, and figure-color-order shortcuts.

## Current decisions

- `EXAMPLES_NEEDED = 4`; ordered production lessons and arbitrary labelled-query rotations are supported against the declared rivals.
- Exact overrides remain observable for all six declared axes; unknown/invalid combinations are rejected.
- Prior behavior accepted malformed `sample_index` values. It now requires an exact nonnegative integer before context construction. This reverses the accidental coercive behavior because identity coordinates must not alias `True`, floats, strings, or negatives.
- Version remains `3.0.0`: the repair does not alter any valid generated grid.
- Racket/canonical authority is unchanged (`RULE_HASH c5cd0106e07a`).

## Evidence

Final generator SHA-256: `1eb55e499f3f2d482825a1a84941f7aea65e262a10dc72fbd347984d0ab1148e`. Final battery: 12/12 green. Portable task tests: 49 passed. Valid-call equivalence: 336/336 baseline-equal. Extended census: 300 lessons (100 per band), 1,500 required query rotations, 0 ambiguous, 1,499 unique inputs.

## Known limits / open findings

The census is sampled rather than exhaustive because no `LESSON_SCHEDULE_PERIOD` is declared, and identifiability is only against declared rivals/hooks. Private solve-query labels remain withheld. No unresolved task-local blocker is known.
## Current reviewer considerations

Source SHA-256: `1eb55e499f3f2d482825a1a84941f7aea65e262a10dc72fbd347984d0ab1148e`.

# Decisions for `5f94fa359992`

## D1 — Reject malformed `sample_index` values at the public boundary

**Prior choice:** The generator passed `sample_index` directly to `gen_ctx`; the rationale for accepting Boolean/coercible/negative values is unknown.

**New choice:** Require `type(sample_index) is int` and `sample_index >= 0`. Non-integers raise `TypeError`; negative integers raise `ValueError`.

**Rationale:** `sample_index` is an identity coordinate, not a numeric quantity to coerce. In Python, `bool` is a subclass of `int`, so `isinstance(..., int)` is insufficient. Silent coercion can alias distinct caller mistakes to real training instances and make replay metadata misleading.

**Alternatives rejected:**

- Coerce with `int(sample_index)`: accepts `True`, floats, and numeric strings and hides caller defects.
- Validate only in shared `gen_ctx`: wider behavioral change outside the assigned generator and unnecessary for this repair.
- Reject only negatives: leaves Boolean/float/string aliases.

**Probe/evidence:** The baseline strict-scalar detector is in `checks/before/checks/5f94fa359992_before_defect_lint.log`; the regression covers `True`, `False`, `1.0`, `"1"`, and `-1`; final focused lint is green in `checks/defect-lint/`.

**Failure modes / limitations:** This does not validate `seed`, whose contract is unchanged. Callers relying on undocumented coercion will now receive an explicit error.

## D2 — Put validation before `gen_ctx` construction

**Prior choice:** Unknown; other override validation already lived in `_validate_call`, but `generate()` did not call it before context creation.

**New choice:** Invoke `_validate_call(sample_index, difficulty, overrides)` as the first operation in `generate()`.

**Rationale:** Fail before draw provenance or random state is constructed, and keep all public-call validation in one function.

**Alternative rejected:** Add an isolated `sample_index` check inline. That would leave difficulty/unknown-axis checks disconnected and make future contract drift more likely.

**Probe/evidence:** Source change in `repo/generators/5f94fa359992/generator.py`; after battery 12/12 green.

**Failure modes / limitations:** The validation function currently raises `ValueError` rather than `TypeError` for malformed integer-valued axis overrides (`n_frames`, `frame_size`), preserving existing behavior.

## D3 — Keep generator version `3.0.0`

**Prior choice:** Version `3.0.0` identified the current valid-instance distribution and four-slot curriculum.

**New choice:** Do not bump it for the malformed-call guard.

**Rationale:** Every valid default and exact-override call tested is byte-identical to baseline. Bumping would invalidate caches despite no accepted-instance change.

**Alternative rejected:** Bump to `3.0.1` merely because source bytes changed. That would alter keyed RNG outputs for all legal examples even though the repair is outside their domain.

**Probe/evidence:** `checks/valid-call-equivalence.json` records 336/336 equal calls, including the full 96-combination override matrix.

**Failure modes / limitations:** The equivalence census is broad but finite. The source diff itself is also confined to pre-generation validation.

## D4 — Make task tests portable instead of repository-depth dependent

**Prior choice:** Tests imported a legacy helper and inferred the data root from a fixed `Path(__file__).parents[...]` depth; original rationale is unknown.

**New choice:** Use `reviewer_support.find_root(__file__)`, `canonical_path(ROOT)`, and `canonical_pairs(..., root=ROOT)`.

**Rationale:** The task-test stage copies sources into an isolated runtime with a different path depth. The supported helper binds tests to the selected source/canonical ledger and works in both repository and staged layouts.

**Alternatives rejected:**

- Add the legacy `scripts` tree to the portable runtime: expands the runtime and preserves a deprecated dependency.
- Hard-code a different parent depth: would fix one layout and break another.
- Skip portable tests: would leave 49 useful semantic regressions unverified.

**Probe/evidence:** The retained intermediate failure is `checks/task-tests-portable/progress.log`; the final result is `checks/task-tests/progress.log` with 49 passed.

**Failure modes / limitations:** Future tests must pass `root=ROOT` to every canonical helper; the intermediate failure demonstrates how one omitted call remains visible.

## D5 — Preserve the four-demonstration curriculum and require query rotations in evidence

**Prior choice:** `EXAMPLES_NEEDED = 4`; every four-example window includes one canonical anchor plus three broad profiles.

**New choice:** Preserve that source policy, but verify all five labelled positions as possible queries in the extended census.

**Rationale:** The assignment defect did not implicate curriculum semantics. Changing the schedule would be unrelated and could disturb already-strong named-rival coverage.

**Alternative rejected:** Reduce demonstrations to three in production because a focused test shows some three-demo windows are identifiable. The declared four-example schedule has stronger coverage and matches exported lesson policy.

**Probe/evidence:** `checks/lesson-census.json`: 300 lessons, 1,500 rotations, no ambiguity or errors, required rotation policy.

**Failure modes / limitations:** No `LESSON_SCHEDULE_PERIOD` is declared, so the census does not exhaust all seeds/start states. It checks declared rivals, not all possible shortcuts.

## D6 — Leave Racket/canonical authority unchanged

**Prior choice:** `RULE_HASH = c5cd0106e07a` and the canonical authority set define tight crop, ascending key sort, vertical centering, and one-column gaps.

**New choice:** No authority edits.

**Rationale:** Rule smoke, semantic checks, visible solve, and authority synchronization all passed. The defect was solely malformed generator API input.

**Alternative rejected:** Touch the rule or canonical examples as part of a broad cleanup. No evidence supported such a change.

**Probe/evidence:** The authority-set SHA-256 is `4bdff2d29af7e7a6ee6ef0c8c692440dea5a4b70a72890df304ceb5285f1d21c` both before and after.

**Failure modes / limitations:** Private test labels remain withheld, so solve correctness is reported only for visible examples.

## D7 — Keep peer-audit targets read-only

**Prior choice:** Audit targets were assigned for adversarial review, not repair.

**New choice:** Record source-bound findings and a reusable override-contract probe without editing either target.

**Rationale:** `DUTIES.md` explicitly separates audit findings from repair approval.

**Probe/evidence:** `AUDIT.md`, `checks/audit/override_contract_probe.py`, and `checks/audit/override-probe-results.json`.

**Failure modes / limitations:** The findings identify reproducible contract defects but do not establish a complete repair or training-readiness verdict for those targets.
