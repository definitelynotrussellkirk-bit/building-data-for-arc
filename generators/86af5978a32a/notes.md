# Current notes: 86af5978a32a

## Intended rule

The input contains two equal `k × k` panels (`k=3..5`) joined horizontally or vertically. The panel with 2–4 distinct nonzero colors is the layout; the panel with exactly one nonzero color supplies only its occupied-cell mask. A `k × k` copy of that mask, recolored by the layout cell, is placed in each nonzero layout block of the `k² × k²` output.

## Baseline defects found

The imported generator described a fixed 3×6, layout-left task but actually emitted variable sizes, only horizontal composition, and layout-first scenes. Most advertised controls were inert or permissive, `RULE_HASH` was missing, canonical shape-first/vertical inputs were rejected, and no executable rival/lesson contract existed. The before battery had 5 green, 1 advisory, and 6 failing stages.

## Current design decisions

- Version `4.0.0`; `RULE_HASH = 80100e676959`; four demonstrations are required.
- Exact observable controls are only `half_size`, `orientation`, `layout_position`, `n_layout_colors`, and `color_role`.
- Default sampling follows a four-step profile schedule that always hits an exact canonical dimension/palette profile and crosses both orientations, panel orders, and color-8 roles.
- Layout and shape palettes are disjoint; each panel retains background and spans at least two rows and columns. Shape masks contain at least three cells.
- The strongest canonical-fitting shortcut is `fixed_eight_shape`: all eight canonical labeled pairs put 8 in the shape panel. Generated `layout_has_8` scenes explicitly refute it.
- Declared rivals are `fixed_eight_shape`, `first_half_is_layout`, and `horizontal_only`; task-domain witnesses and `lesson_identifiable` execute each rival.
- Every five consecutive generated pairs, and every one-pair holdout from that window, contain demonstrations that refute every declared rival.

## Verification and evidence

- Final generator SHA-256: `ee84cd19b1f4ccb64bb6a089b497acacae3c195c16fd3fbe100c83c4b3238a0e`.
- Focused portable tests: 174 passed (`checks/task-tests-final/result.json`).
- Final battery: 12/12 stages green (`checks/after-2/checks/86af5978a32a_after_battery_summary.json`).
- Lesson census: 300 lessons, 1,500 pairs, 1,500 query rotations, zero ambiguities/errors (`checks/lesson-census-1.summary.json`).
- Exact color-8 counterexample: `counterexamples/fixed_eight_shape.json`; canonical Racket replay and rival outputs are retained in `checks/fixed-eight-replay.json`.

## Authority and limits

Selected `target_code` copies were aligned exactly to the active canonical `program_solution`; archival `raw_code` remained byte-identical. This is an authority-text synchronization, not a semantic rule change.

The finite rival checks establish resistance only to the declared hypotheses. The sampler intentionally stays within two square panels, `k=3..5`, one-color shape masks, 2–4 layout colors, and exactly one panel containing color 8; it does not claim to cover every lawful extrapolation of the abstract rule.
## Current reviewer considerations

Source SHA-256: `ee84cd19b1f4ccb64bb6a089b497acacae3c195c16fd3fbe100c83c4b3238a0e`.

# Decisions: 86af5978a32a

## D1 — Treat distinct color count as the semantic role signal

**Decision.** Split the input geometrically into two equal square panels. The 2–4-color panel is the layout and the one-color panel is the shape mask.

**Why.** This is the invariant shared by all canonical examples and by the active Racket authority. It works for either panel order and either orientation.

**Rejected alternatives.** “Left/first panel is the layout,” “horizontal only,” and “the panel containing color 8 is the shape.” Each fits some or all canonical examples but is not the intended rule.

**Probe.** All eight canonical labeled pairs pass an independent implementation; the fixed-8 rival fits all eight, while the retained `layout_has_8` counterexample makes it disagree (`checks/fixed-eight-replay.json`).

## D2 — Replace broad or inert metadata with five exact axes

**Decision.** Advertise only `half_size`, `orientation`, `layout_position`, `n_layout_colors`, and `color_role`.

**Why.** Every value is recoverable exactly from returned pixels, and every boundary combination is constructible. This eliminates the baseline’s dead textures and permissive scalar overrides.

**Rejected alternatives.** Retaining “texture,” density aliases, or hidden profile controls would create non-observable or partially honored axes.

**Probe.** The focused suite exhausts 128 boundary combinations across difficulty bands and checks invalid types, ranges, difficulty values, sample indices, and unknown axes. The final override stage is green.

## D3 — Use a four-step canonical-profile curriculum

**Decision.** Default profiles are:

1. 3×6 horizontal, layout first, 3 layout colors, 8 in layout;
2. 8×4 vertical, layout second, 3 layout colors, 8 in shape;
3. 4×8 horizontal, layout second, 2 layout colors, 8 in shape;
4. 8×4 vertical, layout first, 3 layout colors, 8 in layout.

**Why.** Every draw lands on an exact canonical dimension/palette profile while crossing the role-confounding axes. Deterministic schedule coverage makes lesson guarantees testable rather than probabilistic.

**Rejected alternatives.** Pure random mixing can produce a locally ambiguous lesson even when global support is adequate. Repeating literal canonical inputs would add no counterexamples.

**Failure mode.** The schedule is finite and structured; consumers should not mistake it for exhaustive support over all possible panels.

## D4 — Require four demonstrations and make every query rotation identifiable

**Decision.** `EXAMPLES_NEEDED = 4`. Validate every five-pair window under every one-pair holdout.

**Why.** Four demonstrations are enough for this schedule to retain counterexamples to all three declared rivals after any one pair becomes the query.

**Rejected alternative.** Two or three demonstrations can leave fixed-role or fixed-orientation explanations alive depending on the start residue.

**Probe.** Focused tests exhaust consecutive starts and query positions across all bands. The production census materialized 300 lessons and checked all 1,500 rotations with zero ambiguity.

## D5 — Make color 8 an adversarial role axis, not a role rule

**Decision.** Exactly one panel contains 8, alternating between `shape_is_8` and `layout_has_8`.

**Why.** All canonical demonstrations put 8 in the shape, making “8 identifies shape” the strongest concrete canonical shortcut. Moving 8 into the multicolor layout creates an easy-to-audit counterexample while preserving disjoint palettes.

**Rejected alternative.** Omitting 8 entirely would refute the shortcut less directly and move farther from the canonical palette. Allowing 8 in both panels would make the counterexample axis non-exact.

**Evidence.** `counterexamples/fixed_eight_shape.json`; canonical/Racket replay in `checks/fixed-eight-replay.json`.

## D6 — Keep the generated grammar strict but not canonical-literal

**Decision.** Use `k=3..5`, 2–4 layout colors, one shape color, disjoint palettes, at least one background cell in each panel, a shape of at least three cells, and two-axis spatial support for both roles.

**Why.** These constraints avoid empty, full, line-only, or palette-overlap scenes that obscure the intended abstraction while allowing more shapes and sizes than the canonical set.

**Rejected alternative.** A literal canonical-only generator would pass profile checks but provide little distributional value. A fully unconstrained grammar would admit ambiguous role cardinalities or degenerate masks.

## D7 — Pin executable rivals and witnesses in production code

**Decision.** Declare `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`.

**Why.** A prose claim that a shortcut is covered is not replayable. The gate and census can now execute the rival on saved inputs and verify the exact refuting pair.

**Limit.** The rival set is deliberately finite. Passing it does not prove uniqueness among all computable rules.

## D8 — Align selected authority text to canonical without changing archival history

**Decision.** Replace only the two selected `/racket_target/target_code` values with the exact canonical `program_solution`; preserve both `raw_code` values unchanged.

**Why.** The canonical program is active authority. The legacy target used different primitives but already passed execution parity. Exact alignment removes an active-source divergence without rewriting archival evidence.

**Probe.** Before and after file/target/raw hashes are in `checks/authority-manual-review.json`; final `authority_sync`, `rule_smoke`, and `defect_lint` stages pass.

## D9 — Build tests around behavior, not implementation details

**Decision.** Add a portable 174-test suite under the selected task, using `reviewer_support.find_root` and canonical helpers.

**Coverage.** Canonical pairs, independent rule output, canonical-fitting shortcut, all axis boundaries, invalid calls, profile support, schedule branches, every query rotation, exact counterexample, semantic witnesses, malformed scenes, mutation fixtures, determinism, freshness, global RNG neutrality, helper nonmutation, and public schedule contract.

**Evidence.** The suite was observed red before implementation (173 failures, 1 pass) and green after (174 passes), then passed in the isolated task-test runtime.

## 2026-10-24 parametric review: qualified proposal, owner acceptance pending

Built a native episode-fixed `finish` family without changing the approved
production generator (`ee84cd19b1f4ccb64bb6a089b497acacae3c195c16fd3fbe100c83c4b3238a0e`):

- `stamp_only` returns the exact selected canonical Racket bytes
  (`a6914eb76bfb0d5fbd5a1ed0dc1933807388909461277ac7c0d7b2ac830ca2b5`).
- `highlight_largest_component` performs the canonical layout×mask expansion,
  computes 4-connected components on binary post-expansion occupancy, selects
  the unique largest component, and recolors it to 9
  (`6ad1968277250470da4aca819dd4e5ddd31e35a1b5b9db8dc37cf3a7cac48c02`).

This is a substantive sequential dependency: expansion produces the
input-dependent stamped grid; binary occupancy/components produce the selected
cell set and size histogram; the final recoloring requires that exact set.
Differently colored adjacent stamps can merge only in the post-expansion binary
intermediate. The retained color-sensitive counterfactual selects a different
component: protected Racket replay found binary component sizes `[15,10,10,5]`
versus color-sensitive sizes `[10,5,5,5,5,5,5]`, changing the final answer.

The adapter supports 2–6 demonstrations and 1–4 queries, with four distinct
sequential queries used for qualification. Input sampling is independent of the
private setting, so matched requests have identical inputs. A 30×30 output is
not lawful under the approved grammar (`k=3..5`, output side `k²`); the retained
stress case is the maximum lawful 25×25 output.

Evidence:

- focused suite: 201 passed (`checks/86af5978a32a-green-2/result.json`);
- bounded authoring probe: seeds 0/17/97, both settings, six demos and four
  queries, exact labels and a finite four-rival bank
  (`workspace/parametric/evidence/current/authoring-probe.json`);
- native qualification: four jobs, 40 protected-Racket evaluations
  (`checks/86af5978a32a/qualification/qualification.json` and `execution.json`);
- causal witness: `reviewer_replayed`
  (`checks/86af5978a32a/causal/witness.json`);
- two public-only challenge projections passed saved-file structure/privacy
  checks (`checks/86af5978a32a/public-projection-check.json`).

Current disposition: reviewer-ready proposal; exact-source owner acceptance is
still required. No variant is accepted or training-admitted.
