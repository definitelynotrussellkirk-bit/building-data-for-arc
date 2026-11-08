# Comb insertion family

## Design
Infer the gray container from its complete wide horizontal border and the separate narrower gray comb. Align the comb's baseline to the lowest opening in the container's left wall, and its first tooth to the first interior lane. For each lane, move the existing gray-cap/colored stack upward only as far as needed to clear the inserted tooth, clipping above the container's top aperture. Erase the source comb and place it inside the container. Preserve other cells. This is an authored general interpretation checked against all supplied labels, not blind testing.

Two settings: `insert` is the canonical parent; `longest_survivor` compares colored lane lengths in the post-insertion intermediate and recolors the longest surviving column blue (1), breaking ties leftmost. Sampler colors exclude 1/5/0. Source-longest columns must lose to a shorter source column after insertion, so the counterfactual that selects before pushing changes the final answer.

## Implementation and checks
1. Write official-label and hand-derived mechanical tests, then implement Python and complete Racket reference. No stored grids, gold lookup or parent reads at runtime.
2. Construct deterministic 2–6 demonstration / 1–4 query sampling with separate setting and presentation streams, four novel fixed-bank queries, varying lanes/capacities/gray caps/gaps/comb teeth/container positions, including a content-rich 30x30 scene. Two demos contrast survivor selection and physical insertion shortcuts.
3. Add declared rivals for no push, overpush, top packing, filling all capacity, reversed teeth, retaining the source comb, selecting before insertion, first/last/shortest/tallest-tooth selection and mark-all. Run all supported request bounds; retain any concrete failure and repair.
4. Preflight every original label and every setting. Reuse the first target's source-bound audit interface locally (no cross-checkout imports). Verify causal Racket counterfactual and single-query privacy. Run combined tests and generation/reference execution in a relocated copy before packaging.

## Limits
One upright vessel and one separate left-hand comb; 2-cell lane spacing; contiguous source stacks with gray caps above one distinct color per lane. No claim of arbitrary rotations, unrelated extra objects or overlapping apparatus. Original golds are author-visible. Owner registration/qualification/acceptance remain separate.
