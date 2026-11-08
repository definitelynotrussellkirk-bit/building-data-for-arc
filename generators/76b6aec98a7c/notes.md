# Working notes: 76b6aec98a7c

## Current intended task

A hollow color-1 square frame contains one connected source-color motif. A separate dense rectangle contains symbols 2, 3, 4, and 5. The selected Racket rule crops the complete frame interior, interprets each code as 0, 1, 2, or 3 clockwise quarter turns, and tiles those transformed interiors into the output mosaic. The Racket authority and canonical ledger were not changed; `RULE_HASH = "266efcdf916c"`.

## Repaired generator — version 3.1.0

The previous 2.0.1 sampler claimed positional and palette variation but always used the same 3-cell L motif, a frame at `(1,1)`, a code rectangle at `(7,1)`, and several inert controls. It also allowed code samples that did not necessarily demonstrate all four symbol meanings, had only a weak `self_check`, and omitted a rule-hash pin and executable rival contract.

The selected replacement is constructive and finite rather than rejection-heavy:

- exact controls are limited to real observable axes and are either honored literally or rejected;
- frame/code placement covers left, right, above, and below layouts;
- motif sizes 2–4 use connected, full-bounding-box patterns with four distinct rotations;
- every code rectangle is dense and contains all four codes 2–5;
- source colors 6–9 are scheduled across each four-pair lesson;
- one third of default draws anchor exact canonical `(height,width,palette-size)` profiles so the production population retains clean canonical support;
- `self_check`, `observe_overrides`, an independent Python rule mirror, canonical shortcut declarations, executable semantic rivals, and `lesson_identifiable` are source-bound to the selected generator.

## Teaching decision and strongest shortcut

All three canonical demonstrations use source color 6. Therefore the strongest simple canonical-fitting rival is **`fixed_color_six`**: perform the correct crop/rotation/tiling geometry, then recolor every nonzero output cell to 6. It fits all canonical pairs but fails whenever a generated source color is 7, 8, or 9. The exact Racket-backed color-7 witness is retained at `checks/shortcut-witness/witness.json`; the final distribution probe found 90 disagreements in 120 sampled inputs.

The default lesson has three demonstrations plus one query, in sequential sample-index order. Its four-pair schedule crosses source colors and placements; every pair independently contains all four rotation codes. The larger final census materialized 300 lessons / 1,200 pairs and held out every labelled pair once: zero production ambiguities and zero ambiguities in 1,200 query rotations against `fixed_color_six`, `ignore_rotations`, `reverse_rotations`, and `shifted_codes`.

## Reversals made during review

1. **Prior choice:** merely vary outer grid size while preserving canonical object locations. **New choice:** vary actual object placement in four directions. **Reason:** outer padding did not exercise the rule's content-based object discovery and preserved a location shortcut.
2. **Prior choice:** fixed 3×3 interior and fixed L motif. **New choice:** motif sizes 2–4 with a finite asymmetric connected library. **Reason:** fixed shape/size allowed memorized geometry and could make rotations observationally redundant.
3. **Initial repair attempt:** fully generic sizes without exact canonical-profile anchors. **Reversal:** reserve one third of default sample indices for exact canonical dimension profiles. **Reason:** the first full battery passed 11/12 stages but produced 0/60 canonical-profile hits; an intermediate 13/60 remained below the clean 25% floor. The final schedule gives 43/60 pinned hits and passes the gate.
4. **Initial parser assumption:** generated horizontal/vertical layouts had to overlap on their orthogonal projection. **Reversal:** canonical parsing accepts diagonal separation too. **Reason:** canonical examples are legal under the authority but do not share the generated placement style; the focused regression failed 2 cases until this source/validator conflation was removed.

## Final evidence

- Generator SHA-256: `8864562508cdb1eebf9fb13b229f657996bf1ff609dd3376214597e51050c376`.
- Focused task tests: 28/28 pass (`checks/task-tests-green-final/result.json`).
- Required-rotation battery: 12/12 stages green (`checks/after-final/checks/76b6aec98a7c_after_battery_summary.json`).
- Distribution probe: 120/120 unique valid inputs, all declared axes covered, 12/12 Racket comparisons exact, 64/64 query rotations identifiable (`checks/probe-final.json`).
- Lesson census: 300/300 lessons, 1,200 unique inputs, 0 production or rotated ambiguities (`checks/lesson-census-final.json`).
- Post-repair visible solve: revision 1 passes 3/3 visible examples; earlier rule exposure recorded as yes and reference consultation during solve recorded as no (`solve/summary.json`).

## Known limits

The identifiability claim is finite and only against the declared rivals; it is not a proof against every possible hypothesis. The canonical profile anchor intentionally constrains one third of default dimensions, while motif, code, color, placement, and the remaining dimensions continue to vary. Generated frame/code boxes use a one-cell gap and orthogonal overlap for unambiguous constructive placement; the validator and rule mirror accept canonical diagonal placement rather than asserting that this generated style is the whole legal task domain.
## Current reviewer considerations

Source SHA-256: `8864562508cdb1eebf9fb13b229f657996bf1ff609dd3376214597e51050c376`.

# Decisions: 76b6aec98a7c

## D1 — Preserve the selected Racket authority

**Decision.** Change only the Python generator and task-local support files. Keep the canonical Racket rule and canonical ledger byte-for-byte unchanged; pin `RULE_HASH = "266efcdf916c"`.

**Reason.** The rule already implements the intended content-based operation: find the color-1 frame, crop its complete interior, find the separate 2–5 code rectangle, map code `v` to `v-2` clockwise turns, and tile the results. The defect was sampling and teachability, not label semantics.

**Rejected alternative.** Editing the authority to match the old fixed 3×3 motif or a narrower placement grammar. That would silently change the task rather than repair its generator.

## D2 — Replace declared-but-inert axes with observable controls

**Decision.** Retain only `grid_h`, `grid_w`, `motif_size`, `code_h`, `code_w`, `source_color`, and `layout`. Validate unknown keys and domain/type errors before drawing. An exact override is honored literally whenever geometrically compatible; incompatible combinations raise a specific error.

**Reason.** The old `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` declarations either had no effect or encoded diagnostics rather than production choices. A control surface should describe actual input differences, not aspirational metadata.

**Rejected alternatives.** Keeping aliases for compatibility, or making them silently influence RNG only. Both preserve false affordances and make override-gate evidence misleading.

## D3 — Construct legal scenes directly

**Decision.** Place a square frame and dense code rectangle with a one-cell gap in one of four relative layouts. Use a finite precomputed motif library instead of rejection sampling.

**Reason.** Direct construction guarantees termination, separation, and exact controls. The finite motif library can enforce 4-connectivity, full bounding-box use, non-full fill, and a four-element rotation orbit before sampling.

**Rejected alternatives.** Randomly scatter colored cells and recover valid objects by repeated rejection, or continue varying only outer padding. The first is slow and difficult to reason about; the second leaves the semantic geometry fixed.

## D4 — Make each pair expose every rotation symbol

**Decision.** Every code rectangle contains 2, 3, 4, and 5 at least once. Extra cells, when present, repeat a random code.

**Reason.** A single labelled pair then exposes all four code meanings, while multiple demonstrations are still needed to separate source-color and placement shortcuts. This makes lesson assembly robust to query rotation and avoids a query holding the only example of one code.

**Rejected alternative.** Independent uniform code draws. That has richer count statistics but can omit a symbol from all demonstrations, leaving shifted/reversed code rivals alive.

## D5 — Use asymmetric connected motifs of sizes 2–4

**Decision.** Sample connected, full-bounding-box motifs whose four quarter-turns are distinct.

**Reason.** The old fixed L allowed shape memorization. Symmetric motifs make some or all code values observationally identical, weakening the teaching signal even when every code is present.

**Rejected alternatives.** Arbitrary connected motifs including symmetric ones, or a hand-written short motif list. The finite exhaustive library is small at these sizes and gives an auditable invariant without hidden exclusions.

## D6 — Four-pair color/placement teaching schedule

**Decision.** `EXAMPLES_NEEDED = 3`; a production lesson is three ordered demonstrations and one query using sequential sample indices. Source colors cycle 6,7,8,9 and placements cycle left,right,above,below.

**Reason.** All canonical examples use color 6, so `fixed_color_six` is the strongest simple canonical shortcut. Crossing colors and layouts in every four-pair window refutes that shortcut and fixed-placement hypotheses regardless of which pair is held out. Every pair independently refutes rotation-ignoring and code-remapping rivals because all four codes and an asymmetric motif are present.

**Evidence.** `checks/lesson-census-final.json`: 300 production lessons and 1,200 query rotations, with zero ambiguities or errors against all declared rivals.

## D7 — Add a bounded canonical dimension anchor

**Decision.** When grid dimensions are not overridden, every third sample index uses one of the three canonical `(height,width)` profiles; other indices use difficulty-biased values over the full 10–20 × 10–22 domain.

**Reason.** The first generic implementation passed 11/12 stages but had zero exact canonical profiles in the pinned 60-draw census. A first 20% anchor yielded 13/60 and still missed the clean 25% threshold. The one-third schedule yields 43/60 while leaving the rule-bearing motif, code, source color, and placement varied.

**Failure mode considered.** Over-anchoring could recreate a dimension shortcut. The anchor is intentionally limited to dimensions and one third of indices; `checks/probe-final.json` still observes every declared dimension and content axis.

## D8 — Separate legal-domain parsing from generated style

**Decision.** The parser/validator accepts canonical frame and code boxes that are diagonally separated; the generator itself uses orthogonal overlap for simple constructive placement.

**Reason.** The first regression run passed 24/26 tests because the parser accidentally treated the generated layout style as a universal legality condition. Canonical examples disproved that assumption. Parsing now describes the authority-supported task domain, while generation style remains a narrower intentional distribution choice.

## D9 — Declare and execute rivals

**Decision.** Supply `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, semantic witnesses, and `lesson_identifiable` using pure deterministic functions. Include `fixed_color_six`, `ignore_rotations`, `reverse_rotations`, and `shifted_codes`.

**Reason.** Comments that name rivals are not machine-checkable. Executable rivals let the semantic gate and lesson census state which hypothesis survived, on which exact lesson/query position, and against which final source hash.

**Limit.** This is finite evidence against named rivals, not a completeness theorem over all programs.

## D10 — Build a reusable source-bound probe

**Decision.** Add `workspace/probe_distribution.py` and test that it runs portably.

**Reason.** Future reviewers should not need to reconstruct axis coverage, canonical shortcut fit, lesson rotations, and Racket parity from several ad hoc snippets. The probe iterates declarations from the selected source and hashes that source in its report.

**Evidence.** Final run: 120/120 unique valid inputs, 116 unique outputs, complete axis coverage, 64/64 lesson rotations, 12/12 Racket comparisons, and disagreements for every declared rival (`checks/probe-final.json`).
