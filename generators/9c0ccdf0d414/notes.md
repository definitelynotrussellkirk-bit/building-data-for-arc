# Working notes: 9c0ccdf0d414

## Current rule and domain

The pinned canonical authority is `RULE_HASH = "559cd5677fd5"`. It finds same-color 4-connected motifs, assigns each motif to TL/TR/BL/BR by its cell centroid, tightly crops it, and pastes the **first** motif from each quadrant into the corresponding cell of a 2×2 output mosaic. Mosaic rows and columns use the maximum crop dimensions in their two slots, with one zero gutter row and column.

The selected generator is version `2.0.0` and deliberately emits only the lossless part of that authority domain: exactly three or four motifs, distinct colors, three to six cells each, and at most one motif per centroid quadrant. No Racket authority changed in this review.

## Defect closed

Lead used: retained audit `review-05f12ae0dce0712e:v0001` against source SHA-256 `7210e50e517cc91bd10bc7bebfa908d22bde8bded6b83648f91a13974438d383`. Its seed-0/sample-0 witness placed colors 3 and 6 in BR; the authority kept the first and silently omitted color 6. The former rejection sampler therefore generated inputs whose labels discarded a real motif while `self_check()` accepted them.

Repair: replace unconstrained scattering with constructive, separated quadrant placement. `_safe_quadrants` reserves a blank central row/column band; `_placement_origin` places each crop at an observable outer or inner corner; `strict_canonical_like` rejects duplicate quadrants and verifies that input and output nonzero color sets agree. The old acceptance-only checker and dead/unobservable axes were removed.

## Input and curriculum decisions

Advertised exact controls are intentionally small and pixel-recoverable:

- `grid_h`, `grid_w`: literal integers 8..14;
- `n_motifs`: 3 or 4;
- `palette_kind`: one of four fixed, distinguishable color families;
- `position_style`: outer or inner alignment in each safe quadrant.

Unknown keys and invalid scalar types are rejected. `observe_overrides()` independently recovers all four controls from pixels. The 3×3 polyomino catalogue excludes full-3×3 bounding boxes so outer/inner remains observable even on an 8×8 canvas.

A five-state cyclic schedule covers missing TL, TR, BL, BR, then all four quadrants. The first four profiles hit the canonical dimension/palette signatures. Every five-pair lesson contains four demonstrations plus one query and, under every query rotation, refutes both declared generated-lesson competitors: color-sorted packing and occupied-quadrant compression. Only color-sorted packing is declared a `CANONICAL_SHORTCUT`, because it alone fits every canonical pair.

## Verification

Final generator SHA-256: `affda74a065d4074e7a58218f46fee4c2c8627cb4fe691e4e23e654dd0489a81`.

- Task-local regression suite: 19 passed, 0 failed/skipped/errors (`checks/task-tests-green-3/result.json`).
- All 12 inherited stages passed independently on those exact generator bytes (`checks/final_gate_matrix.json`).
- Required lesson census: 300/300 lessons materialized, 1,500 pairs and 1,500 query rotations, 0 ambiguities/warnings/errors, 1,495 unique inputs (`checks/lesson-census-final.summary.json`).
- Exposed post-repair solve: revision 1 passed 4/4 visible examples; earlier authority exposure was recorded honestly.

Two aggregate-battery attempts were retained as tooling failures, not source failures: the generated resume command omitted the pinned Racket directory from `PATH`, and a fresh aggregate run remained stuck at `defect_lint` beyond the script's stated 300-second child cap. Every constituent stage was rerun separately using the packet's documented per-stage path.

## Limits and self-review

The finite rival set is not a proof of unique induction against every conceivable program. The generator intentionally excludes multiple motifs in one quadrant, centerline-centroid ties, overlapping/crossing motif crops, and disconnected same-color motifs; these are authority behaviors outside the selected training domain. Fixed palette families make exact controls observable but do not attempt full color-permutation coverage.

Shortcut self-review: the schedule varies which quadrant is absent and permutes color-to-quadrant assignment away from ascending color order, so neither color sorting nor compression into leading slots survives a four-demonstration lesson. The retained lossless invariant is checked directly rather than inferred from morphology alone.
## Current reviewer considerations

Source SHA-256: `affda74a065d4074e7a58218f46fee4c2c8627cb4fe691e4e23e654dd0489a81`.

# Decisions: 9c0ccdf0d414

## D1 — Treat the retained audit as a real label-preservation defect

**Prior choice:** v1.1.1 scattered 3–5 motifs anywhere and trusted the authority to produce a label. Its checker validated generic motif shape but not the authority's first-per-quadrant selection.

**Evidence:** retained return `review-05f12ae0dce0712e:v0001`, old source SHA-256 `7210e50e517cc91bd10bc7bebfa908d22bde8bded6b83648f91a13974438d383`. Seed 0/sample 0 placed two motifs in BR and lost color 6 from the output.

**Decision:** define the training domain as the lossless subset of the existing authority: at most one motif per centroid quadrant, with every input color present in the output.

**Rejected alternatives:** changing the authority to keep multiple motifs per quadrant would alter the canonical task; preserving unconstrained placement and merely documenting deletion would continue training on semantically discarded input; rejection sampling would be harder to reason about and could create seed-dependent stalls.

## D2 — Construct scenes by quadrant instead of repairing collisions afterward

Each source quadrant receives a safe rectangular region separated from the center by blank rows/columns. A connected 3–6-cell shape is selected from a finite 3×3 catalogue and anchored at either the outer or inner corner of that region.

Constructive placement makes quadrant uniqueness true by design, keeps colors disconnected, and avoids unbounded retry loops. Full-3×3 bounding boxes are excluded so the outer/inner axis remains distinguishable at the minimum 8×8 size.

Failure modes checked: duplicated quadrants, merged same-color components, motifs below three cells, output color loss, centerline ambiguity, and global RNG mutation. The focused suite contains direct impostors for the first three.

## D3 — Keep only controls that are observable from returned pixels

The public controls are:

- `grid_h` and `grid_w`, 8..14;
- `n_motifs`, 3 or 4;
- `palette_kind`, four fixed color families;
- `position_style`, outer or inner.

Every control is recoverable through `observe_overrides()`. Unknown keys and malformed scalar types are rejected before generation. Difficulty remains a sampler context rather than a claimed axis.

**Rejected alternatives:** density, free-form positional bias, and arbitrary palette size were removed because the baseline gates found them dead, texture-equivalent, or not reliably observable. Random color subsets were rejected for this version because they make a named palette-family override non-identifiable.

## D4 — Use five cyclic profiles to teach quadrant identity

Profiles omit TL, TR, BL, and BR in turn, followed by an all-four case. The lesson shape is four demonstrations plus one query. Five consecutive accepted samples therefore cover the full profile set, and any held-out query leaves four demonstrations that still refute every declared lesson competitor.

The first four profiles deliberately match the measured canonical dimension/palette signatures `(8,8,3)`, `(9,9,3)`, `(9,10,3)`, and `(10,10,3)`; the all-four profile broadens dimensions by difficulty.

The finite rivals are:

1. sort motifs by color and paste into leading slots;
2. ignore source quadrant identities and compress row-major motifs into leading slots.

Only rival 1 fits every canonical pair, so only it is declared under `CANONICAL_SHORTCUTS`. Both remain `LESSON_COMPETITORS` and are refuted under all query rotations.

## D5 — Preserve the authority, pin it, and mirror it for tests

No Racket source changed. `RULE_HASH = "559cd5677fd5"` binds the selected generator to the canonical authority. The Python mirror exists only for authoring/tests and is checked against every canonical pair; `rule_smoke`, `racket_lint`, and `authority_sync` independently passed.

Changing the rule was rejected because the reported defect was distribution/label alignment, not a canonical-rule error.

## D6 — Use per-stage evidence after aggregate-controller failure

Two aggregate attempts were retained. The first resume lacked Racket on `PATH`; the second remained at `defect_lint` beyond its own 300-second stage cap. The packet's battery script explicitly documents per-stage execution for environments with foreground caps.

Decision: rerun every constituent stage independently, require its runtime manifest to contain the final generator hash, and build `checks/final_gate_matrix.json` programmatically. No interrupted aggregate is called a pass.

## D7 — Limits accepted for this version

The generator does not teach multiple motifs in one quadrant, centerline centroid ties, overlapping/crossing crops, or disconnected same-color motifs. These are outside the selected lossless training grammar. The 300-lesson census checks only declared rivals and sampled seeds; it does not prove universal program identifiability.
