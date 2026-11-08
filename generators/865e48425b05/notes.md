# Working notes: 865e48425b05

## Review-eebf4016de087172 (2026-10-05)

Baseline `1.1.1` advertised nine mostly dead or duplicated controls, omitted `RULE_HASH`, generated only 2–3 palette entries and four small masks, rejected two of five canonical inputs, and had no executable teaching contract. The before battery on generator SHA-256 `980faaadc540b8cb54cd167d66c85db2d7b2f546859e069c40d979aa54f1d4b0` finished with 5 green, 1 advisory, and 6 failed stages.

Version `2.0.1` pins rule `efb1009fca26`, replaces the dead surface with four exact pixel-observable axes, accepts all five canonical pairs, supports 2–4 palette colors and twelve connected masks, and validates the complete task grammar. The Racket authority was not changed.

The curriculum repeats four profiles: canonical/sorted, broad/unsorted, canonical/unsorted, broad/sorted. Thus every four consecutive examples—and every three-demo set formed by holding one out—retains at least one non-3x3 mask and one unsorted palette. Declared rivals are fixed 3x3 cropping, numeric palette sorting, no inter-copy gap, and solid bounding-box fill.

Final evidence is source-bound to generator SHA-256 `e2f12c1139f6fea5940fe2ccc7cbe4cc9ee81f07f992abda8953273e508beff9`:

- `checks/after-final/checks/865e48425b05_after_battery_summary.json`: 12/12 green.
- `checks/task-tests-final2/result.json`: 32/32 task-local tests passed, including real Racket parity.
- `checks/lesson-census-final.json`: 300 lessons, 1,200 unique labelled inputs, 1,200/1,200 rotations checked, zero declared-rival ambiguities or scoring errors.
- `checks/review-probe-final.json`: all 3,456 joint exact-axis cases, 144 cyclic starts, 576 held-out rotations, and 29 Racket parity cases passed.

Finite rival testing does not prove unique induction against every conceivable rule. The grammar intentionally restricts masks to twelve connected templates and palettes to colors 2–9; this is broader than canonical support but not an unconstrained polyomino generator. Difficulty changes lawful profile scale/mask selection rather than the endpoint concept.
## Current reviewer considerations

Source SHA-256: `e2f12c1139f6fea5940fe2ccc7cbe4cc9ee81f07f992abda8953273e508beff9`.

# Decisions — generator 865e48425b05

Assignment `review-eebf4016de087172`; final generator version `2.0.1`; final SHA-256 `e2f12c1139f6fea5940fe2ccc7cbe4cc9ee81f07f992abda8953273e508beff9`.

## D1 — Keep the canonical Racket authority unchanged and pin it

**Choice.** Added `RULE_HASH = "efb1009fca26"` and left the canonical Racket program untouched.

**Rationale.** All five public canonical pairs and independent Python reconstruction agree with the selected authority. The baseline rule-smoke and authority-sync stages were already green; the defects were in generation, validation, metadata, and teaching support rather than the endpoint transformation.

**Alternatives considered.** Rewriting or beautifying the Racket rule was rejected because it would add authority risk without changing behavior. Leaving the hash unpinned was rejected because it made source/rule drift invisible.

**Probe.** `checks/review-probe-final.json` compares 29 canonical/generated inputs against real Racket output; zero mismatches. The final battery's rule-smoke and authority-sync stages are green.

**Limitation.** The Python oracle is independent code but still a finite implementation check; canonical authority remains Racket.

## D2 — Replace the imported generic axis surface with four exact controls

**Choice.** Retained only `grid_h` (7..10), `grid_w` (9..14), `n_palette` (2..4), and `mask_id` (0..11). Added strict type/range validation, unknown-key rejection, exact `GenCtx` provenance, `observe_overrides`, and declared the full cross-product constructive.

**Original rationale.** Unknown. The baseline advertised nine controls, but several were aliases, singleton labels, or never consumed (`palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and most `texture` values). This looked like imported generic metadata rather than a task-specific design.

**Alternatives considered.** Keeping cosmetic aliases for compatibility was rejected because an accepted but ignored override is worse than a loud migration error. A free-form shape axis was rejected because exact pixel recovery would be ambiguous and the override matrix would become unbounded.

**Probe.** The task-local deep probe exhausts `4 × 6 × 3 × 12 × 4 = 3,456` joint axis/difficulty combinations and independently recovers every requested value with zero failures. The shared override stage is green.

**Failure modes.** Any future mask addition must update both production and the independent catalogue/test. Retired override names now fail loudly and may require downstream caller migration.

## D3 — Use twelve connected masks, separating canonical and teaching shapes

**Choice.** IDs 0–5 are 3x3 canonical-like masks with 5–6 cells; IDs 6–11 are connected non-3x3 shapes ranging from 2x2 through 4x3. All fit the minimum 7x9 canvas below an empty separator row.

**Rationale.** The five canonical examples all use 3x3 masks, so canonical-only support admits a fixed-3x3 shortcut. Non-3x3 masks are the smallest direct counterexamples while preserving the same crop/recolor rule. Including canonical masks protects profile fidelity and accepts every canonical input, including the 4-color/6-cell cases rejected by the baseline validator.

**Alternatives considered.** Arbitrary random polyomino generation would broaden shape diversity but make exact `mask_id` controls and independent exhaustive testing harder. Retaining the baseline's four 3–5-cell shapes was rejected because it rejected two canonical examples and under-covered the rule.

**Probe.** Canonical pair tests identify IDs 0–4 exactly. The fixed-3x3 rival fits all five canonical outputs and is refuted by every broad scheduled example.

**Limitation.** Twelve templates do not span all connected polyominoes. This is a deliberate bounded grammar, not evidence that the rule generalizes to every possible mask.

## D4 — Use a four-example rotation-safe teaching cycle

**Choice.** The public schedule repeats:

1. `canonical_sorted`
2. `broad_unsorted`
3. `canonical_unsorted`
4. `broad_sorted`

Any four consecutive samples contain two non-3x3 masks and two deliberately unsorted palettes. Holding out any one pair leaves at least one witness of each type among the three demonstrations.

**Rationale.** Correct labels are insufficient when demonstrations support a plausible wrong rule. The cycle specifically refutes both the fixed-3x3 canonical shortcut and numeric color sorting under every query rotation, while every example also refutes no-gap and solid-bounding-box rivals.

**Alternatives considered.** Independent random witness sampling was rejected because frequency does not guarantee every assembled lesson contains a counterexample. An order-dependent curriculum was rejected because downstream assembly may rotate the query. More than four profiles added no demonstrated teaching benefit.

**Probes.** `checks/review-probe-final.json` checks 48 cyclic starts per band (144 starts, 576 rotations) with zero failures. `checks/lesson-census-final.json` checks 300 production lessons, 1,200 unique pairs, and 1,200 rotations with zero declared-rival ambiguities or scoring errors.

**Limitations.** This is finite evidence against four declared rivals, not universal uniqueness. Sample indices are not exposed to the model, but the schedule itself is periodic.

## D5 — Make difficulty lawful and observable without changing the concept

**Choice.** Difficulty shifts which canonical profile and mask ID a schedule block uses. It does not change the rule, declared axis ranges, or witness cycle.

**Rationale.** The first repaired version produced byte-identical easy/medium/hard instances and correctly failed defect-lint. Difficulty now changes scale/palette cardinality/mask selection while retaining canonical support in every band.

**Alternatives considered.** Ignoring difficulty was rejected after the reproducible dead-band warning. Making hard examples use a different semantic rule was rejected as label drift. Difficulty-specific override ranges were rejected because exact controls should mean the same thing in every band.

**Probe.** A regression test first demonstrated identical bands, then passed after the change. Final defect-lint is green and exact overrides pass at both boundaries in all bands.

**Limitation.** Difficulty reflects input variation, not a calibrated human/model difficulty score.

## D6 — Validate the complete input grammar, not just cell counts

**Choice.** `self_check` now requires a rectangular integer grid, dimensions 7..10 by 9..14, 2–4 distinct row-0 colors from 2..9 separated by zeros, a blank row 1, only 0/1 below the legend, and one recognized 4-connected mask. It rejects bool/float cells, duplicate colors, foreign colors, disconnected/unrecognized shapes, ragged rows, and mismatched override metadata.

**Rationale.** The baseline validator accepted malformed scenes and rejected lawful canonical 4-color/6-cell scenes. A strict validator is needed for distribution gates, mutation checks, and trustworthy exact-axis observations.

**Alternatives considered.** A permissive “any connected mask” validator would accept scenes the generator and exact `mask_id` contract cannot reproduce. A validator tied to RNG bookkeeping was rejected; all observations come from pixels.

**Probe.** Targeted mutation tests and shared self-check/grammar stages pass. All five canonical inputs are accepted by both `self_check` and `strict_canonical_like`.

## D7 — Declare executable rivals and witnesses

**Choice.** Added pure deterministic rivals for fixed 3x3, sorted palette, no gap, and solid bounding box, with corresponding witnesses and a finite `lesson_identifiable` check. Only fixed 3x3 is declared a canonical-fitting shortcut.

**Rationale.** These are simple, plausible local misunderstandings of the visible transformation. They cover shape normalization, palette order, spacing, and sparsity—the four information-bearing parts of the rule.

**Alternatives considered.** A large speculative rival catalogue was rejected because unmotivated rules create noise and false confidence. A witness-only contract was rejected because witness frequency does not prove the rival is actually refuted in each lesson.

**Probe.** Tests verify rival purity, canonical fit where claimed, real counterexamples, every query rotation, and agreement with independently written rival functions.

**Limitation.** Undeclared rivals remain possible. The contract explicitly makes a finite claim only.

## D8 — Add independent reusable review tools and tests

**Choice.** Added:

- `workspace/reference_probe.py`: independent oracle, mask catalogue, canonical loader, observers, rivals, and Racket helper.
- `workspace/review_probe.py`: exhaustive axis matrix, cyclic lesson rotations, shortcut checks, and optional Racket parity.
- `tests/test_generator.py`: 32 portable regression tests.

**Rationale.** Tests that call production helpers can duplicate the same bug. The independent module intentionally repeats the compact rule and mask contract rather than importing implementation internals.

**Alternatives considered.** One-off shell snippets were rejected because future reviewers could not replay them. Importing private `scripts.*` helpers was rejected for portable-layout compatibility.

**Probe.** Portable task-test stage: 32 passed, 0 failed/error/skipped. The review probe passes all 3,456 axis cases, 576 rotations, and 29 real-Racket comparisons.

## D9 — Preserve failed iterations and exposure truthfully

**Choice.** Retained the failed before battery and the intermediate dead-band battery. Kept one genuine blind-solve revision and one genuine post-repair revision; did not manufacture negative attempts. The post-repair solve declares earlier rule exposure `yes` and reference consultation during the solve `no`.

**Rationale.** Failed evidence is useful for regression and prevents a misleading all-green narrative. The post-repair solve cannot honestly be called blind after generator work.

**Limitation.** Both solve checkers withhold private query correctness; visible-example success is not a private-label score.

## Review-c8b8a427b8f4d43c — native parametric candidate (2026-10-24)

The production generator remains version `2.0.1` at SHA-256
`e2f12c1139f6fea5940fe2ccc7cbe4cc9ee81f07f992abda8953273e508beff9`;
the canonical Racket authority was not edited. This review adds a task-local
`layout_policy` family under `workspace/parametric/`:

- `horizontal` is the exact canonical program, byte for byte.
- `vertical` stacks recolored mask copies with one blank row between copies.
- `dominant_axis` crops the color-1 mask, measures its bounding box, and chooses
  horizontal packing when width is at least height, otherwise vertical packing.

The first two demonstrations use one wide mask and one tall mask. Their output
axis signatures distinguish all three settings from demonstrations alone:
`HH`, `VV`, and `HV`. The adapter supports 2–6 demonstrations and 1–4 queries;
qualification uses three demonstrations and four sequentially revealed queries.
The public turn projection exposes no hidden setting, program, answer, seed, or
future-query count. Four query profiles include a 30×30 stress input.

The required sequential dependency is genuine: A crops and measures the mask;
the intermediate value is its height, width, and dominant axis; B packs copies
along that axis. A source-bound `skip_a` counterfactual substitutes canonical
horizontal packing for a tall-mask `dominant_axis` case and changes the final
output under protected Racket.

Retained evidence:

- `checks/865e48425b05/final-tests/focused.stdout`: 27 focused tests passed.
- `checks/865e48425b05-tests/result.json`: 59/59 task tests passed in 17.28 s.
- `checks/865e48425b05/audit-v1/report.json`: 18 episodes, 138 labels, 288
  protected-Racket evaluations, zero harmful named-rival survivors, zero
  Python/Racket mismatches, and zero public-projection failures.
- `checks/865e48425b05/qualification/qualification.json`: native qualification
  passed for three settings × two seeds, with three demonstrations and four
  queries per job; `execution.json` retains 78 protected-Racket evaluations.
- `checks/865e48425b05/causal/witness.json` and `causal/replay.json`: native
  source-bound witness schema and protected replay; witness SHA-256
  `82e5a11e8656aaad3aed82c15d87baf8de2ea6faa6fbe3ddc3af83566e76f62b`.
- Task-local manifest SHA-256:
  `38a379e395c6b53584d405a07194bf55568e5a341000e1f724803fe9e55b9bd3`.

This is finite evidence against the declared rivals and sampled counts/seeds,
not a proof of unique induction or measured training gain. Native status remains
owner-pending: exact-source integration and fresh owner acceptance replay are
still required, and no training admission is claimed.
