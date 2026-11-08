# Working notes: 600284beb8e4

## Canonical repair

The canonical rule remains byte-for-byte unchanged: recover the bounding boxes
of the color-2 and color-3 rectangular borders and paint their nonempty
intersection with color 8. `RULE_HASH` is pinned to `0460c3a13fef`.

The imported sampler had a concrete teaching defect: color 2 was always north
of color 3, so a positional shortcut (use color 3's top through color 2's
bottom) matched the full generated distribution. The repaired sampler exposes
only observable controls and constructively covers six role relations:
`2_north`, `2_south`, `2_west`, `2_east`, `2_horizontal`, and `2_vertical`,
with interior and boundary-touching forms. Its strict checker requires two
recoverable rectangular borders and a nonempty bbox intersection. Request
validation rejects booleans/coercions, negative indexes, invalid difficulties,
and unknown or mistyped overrides.

## Parametric family

The native task-local family has one episode-fixed parameter, `edge_policy`:

- `full`: exact canonical program and full rectangle intersection.
- `near_cue`: locate the unique color-1 cue, infer which side of the overlap it
  indicates, then paint that overlap edge.
- `far_cue`: use the same inferred side but paint the opposite overlap edge.

A is cue localization and side inference; the intermediate is one of
`north/east/south/west`; B consumes that side to select an overlap boundary.
Inputs are byte-identical across settings. The API supports independent 2–6
training examples and 1–4 returned queries; the retained private bank always
contains four distinct queries, with an actual distributed 30×30 fourth scene.
The query bank is prefix-stable for sequential reveal.

The minimum two demonstrations use different cue sides. A first repair crossed
the cue opposite color 2, but adversarial review found that this made
"farthest from color 2" a complete bypass. The final pair crosses the cue on a
perpendicular axis to color 2's extension, defeating both nearest-color-2 and
farthest-color-2 shortcuts without increasing the lesson count.

## Retained checks and limits

Focused tests cover canonical pairs/hash, exact control observability,
distribution coverage, strict request and grid rejection, determinism/freshness,
matched inputs, count independence, minimum-demo setting identification,
fixed-edge and rectangle-role shortcuts, and 30×30 content.

`workspace/parametric/audit.py` is a reusable bounded adversarial tool. The
retained run uses 96 seeds, minimum and maximum demo counts, all three settings,
fixed-edge, frozen-first-side, full/near/far, color-2-near/far attacks, crossed
controls, malformed requests, and protected-Racket labels. This is finite
counterevidence to named shortcuts, not a universal uniqueness proof.

Owner source review, native qualification/acceptance, and training admission
remain downstream decisions; no approval flags were changed here.
