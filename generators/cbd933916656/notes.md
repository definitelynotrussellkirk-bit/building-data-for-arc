# Working notes: cbd933916656

## 2026-10-25 — full native parametric prototype

The reviewed production generator and canonical authority were left unchanged. The default `finish_mode=rank_only` returns the exact selected canonical Racket bytes (SHA-256 `ae575d29554f957261f53f7ebe474e1122b0277c2f81eae526af838e8385e30a`).

The added `selector_bbox` setting first performs the canonical operation: discover three separated same-color components, rank them by cardinal perimeter with size/bounding-box tie-breaks, and recolor ranks 0/1/2 as 2/4/8. The common original object color is an episode input selector: 1 chooses rank 0, 3 chooses rank 1, and 5 chooses rank 2. The selected ranked component's bounding box is then filled with its Step-A rank color.

The sampler deliberately uses a compact shape with a hole, an L path, and a hollow ring. Their perimeter order is distinct and differs from occupied-area order; positions and orientations vary independently, and every component gains cells under the bounding-box fill. The first three demonstrations exercise selector colors 1, 3, and 5.

Retained checks:

- 13 direct tests and 13 copied-runtime task tests pass.
- The 16-seed audit checks 160 generated pairs, 128 count prefixes, 64 fixed-rank/area-rank rivals, all three selected ranks across varying positions, a substantive 30×30 query with 106 nonzero cells, and 32 ordinary base draws.
- The authoring preflight passes four jobs (two settings × seeds 0 and 17), with three demonstrations, four queries, and 40 protected-Racket label evaluations.
- The protected causal witness shifts the selector's rank-color mapping to the next rank; the qualified and counterfactual programs produce different final outputs.
- Public projection checks cover 16 one-query views for this target and participate in the combined 8 first-turn / 48 private-field-invariance / 8 positive-control report.

Limits: the audit attacks named finite rivals, not every possible shortcut. The base remains unapproved, and the family is reviewer-ready only; owner source review, native qualification/acceptance, and any training admission are still separate.
