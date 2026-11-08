# Current notes: `44756e464c2d`

## Intended rule and authority

Blue(1) cells on the top border select columns; red(2) cells on the left border select rows. The output is an otherwise-zero grid with green(3) at the Cartesian product of selected rows and columns. Canonical Racket behavior is unchanged and pinned at rule hash `a5adc22c1318`; generator version is `2.0.0`.

## Current production design

- Exact axes: `grid_h=7..10`, `grid_w=8..10`, `n_row_marks=1..4`, and `n_col_marks=1..4`.
- All explicit values are supported in every band; unknown/invalid controls fail loudly.
- Inputs use only canonical colors `{0,1,2}`, keep the origin/interior zero, and contain lawful border selectors.
- Four-step schedule: canonical, red-on-top distractor, blue-on-left distractor, both distractors.
- Role-swapped distractors are ignored by the authority and refute the canonical-fitting shortcut `all_nonzero_border_cells_select`.
- Every three consecutive pairs contain at least two witnesses, preserving one in the demonstrations under every one-query rotation.

## Reversed choices

The imported generator's broad nominal axes, dead palette/texture aliases, single-valued controls, invalid production negatives, permissive validator, and missing rule pin were removed. The original rationale is unknown because imported notes were empty.

An intermediate repair used an extra distractor color. Although semantic checks passed, profile floor failed at 13/60 because the palette left the canonical envelope. It was replaced with role-swapped canonical colors, raising final support to 48/60 exact and 60/60 envelope while preserving the same teaching contrast.

The selected duplicate Racket `target_code` was synchronized exactly with canonical `raw_code`; behavior did not change.

## Evidence

Final generator SHA-256: `c02283625ebe2431743d613a4e1173702ac337885d10d956b6c58976b66638a3`.

- Full battery: 12/12 green (`checks/after-v2/`).
- Portable focused tests: 40/40 (`checks/task-tests-final-v3/`).
- Random lesson census: 300 lessons, 1,200 pairs, 1,200 rotations, 0 ambiguity, 1,131 unique inputs.
- Fixed-seed schedule census: 12 starts and 48 rotations, 0 ambiguity.
- Retained witness: `counterexamples/role-swapped-border-colors.json`.

## Known limits and open findings

The teaching claim covers the executable declared rival over the tested sampler. It is not a proof of unique induction against arbitrary hypotheses or all seeds. The chosen domain intentionally stays within the tested canonical size/palette envelope. No open blocker remains for this repair; catalog approval/training admission remains outside reviewer authority.
## Current reviewer considerations

Source SHA-256: `c02283625ebe2431743d613a4e1173702ac337885d10d956b6c58976b66638a3`.

# Decisions for `44756e464c2d`

## D1 — Preserve the canonical transformation

**Choice.** Keep the canonical Racket behavior unchanged and pin `RULE_HASH = "a5adc22c1318"`.

**Why.** Public labels, real-Racket smoke tests, grammar, and execution parity all passed. The defects were in generator truthfulness, domain validation, profile support, teaching evidence, and duplicated authority text—not in the transformation.

**Alternative rejected.** Rewriting the rule around generated inputs would risk narrowing or changing the actual ARC task without evidence.

## D2 — Replace ten nominal controls with four exact observable axes

**Choice.** Retain only `grid_h`, `grid_w`, `n_row_marks`, and `n_col_marks`.

**Baseline.** The old module advertised palette aliases, palette size, distinct-color count, position bias, density, and texture. Most were ignored or single-valued; negative fixtures shared the ordinary texture domain. The original rationale is unknown because the imported notes were empty; the docstring suggests breadth was intended, but the implementation did not realize it.

**Why.** A small truthful control surface is more useful for reproducible training data than a large fictional one. Every retained axis changes returned pixels and is reconstructed by `observe_overrides`.

**Alternatives rejected.** Keeping `palette_kind`, `palette_size`, or `n_distinct_colors` would be dishonest because the canonical rule gives fixed selector colors. Keeping single-valued `position_bias` or `density` adds no controllable variation. Keeping malformed negatives in `texture` mixes diagnostics with production.

## D3 — Use the canonical envelope as the production shape/count domain

**Choice.** Generate heights 7–10, widths 8–10, and 1–4 selectors of each role.

**Why.** These dimensions cover the three linked canonical profiles (7×8, 9×9, 10×10), support all four selector counts plus a distractor slot, and passed strict/profile checks in every band.

**Alternative rejected.** The old nominal 5–14 range had no canonical support at its extremes and created incompatibilities between requested counts and available border slots. A broader domain could be added later only with explicit joint constraints and evidence.

## D4 — Teach the canonical-fitting shortcut explicitly

**Choice.** Declare `all_nonzero_border_cells_select` as a canonical-fitting rival and `color_specific_border_roles` as its witness.

**Why.** All public pairs contain only blue on top and red on left, so a color-agnostic nonzero-border rule fits every canonical label. Role-swapped lawful colors create a minimal contrast: red on top and blue on left must be ignored.

**Alternative rejected.** Merely varying counts, positions, or grid sizes never separates the rival. Randomly hoping for a useful contrast provides no lesson-level guarantee.

## D5 — Use a deterministic four-profile schedule

**Choice.** Cycle `canonical`, `top_distractor`, `left_distractor`, and `both_distractors`, independent of band.

**Why.** Every three consecutive generated pairs contain at least two witness-bearing inputs. Under the normal two-demo/one-query assembly, every possible query holdout therefore leaves a witness in the demonstrations.

**Probes.** The task-local test exhausts all four starts across all bands. The source-bound schedule census independently materialized all 12 starts at seed 0 and checked all 48 query rotations.

**Limitation.** A fixed-seed schedule census verifies declared residues, not all random support or arbitrary downstream reordering.

## D6 — Reverse the intermediate extra-color distractor design

**Prior choice.** The first repair used a fourth input color for distractors. It passed 11/12 gates and the semantic checks, but exact/envelope profile support was only 13/60 (21.7%), below the 25% profile floor (`checks/after-v1/`).

**New choice.** Use canonical role-swapped colors instead: red(2) on top and blue(1) on left.

**Why.** This preserves the exact `{0,1,2}` input palette while producing the same semantic counterexample. The final profile result rose to 48/60 exact and 60/60 envelope without weakening the rival witness.

**Alternative rejected.** Artificially increasing canonical-only schedule frequency would satisfy the numeric floor but reduce teaching density. Role-swapped colors solve both concerns directly.

## D7 — Make validation structural and fail overrides loudly

**Choice.** Reject unknown override keys, non-integer/bool values, out-of-range values, ragged/noninteger grids, interior marks, unknown colors, bad origins, and unsupported selector/distractor counts.

**Why.** The old `self_check` only verified nonempty selectors and origin zero. That allowed malformed structures and made exact-control failures easy to hide.

**Alternative rejected.** Silent clamping or fallback destroys experiment reproducibility. Declared incompatibility was unnecessary because every retained axis combination is constructible.

## D8 — Synchronize duplicate authority text exactly

**Choice.** Set the selected bank record's `racket_target.target_code` to its canonical `raw_code`.

**Why.** Before repair, active sources were behaviorally equivalent but exact-text divergent, failing authority sync. Exact synchronization removes ambiguity about which source reviewers and runners are evaluating.

**Scope.** Canonical behavior, callable hash, and rule hash did not change.

## D9 — Retain independent probes, a counterexample, and portable tests

**Choice.** Add `workspace/reference_probe.py`, focused tests, and `counterexamples/role-swapped-border-colors.json`.

**Why.** The independent Python mirror makes control/structure failures easy to diagnose, while real-Racket battery/census runs remain the label authority. The retained fixture prevents future removal of the teaching contrast.

**TDD record.** The initial focused suite failed 24 cases before production edits; a profile regression failed before the palette revision; the retained-counterexample test failed before the fixture existed. Final portable suite: 40/40.

## D10 — Bound the conclusion

The final result establishes truthful exact controls, canonical support, strict validation, and no ambiguity against the declared canonical-fitting rival in the tested production and rotation samples. It does not prove that no other shortcut exists, that every possible seed is equally valuable, or that a different lesson assembler preserves the same guarantee. Those limits are documented rather than converted into unsupported approval claims.
