# Solve work log

## Exposure declaration

This is not an independent blind inference. Before this post-repair solve episode I had already inspected the task family while repairing its generator and had therefore seen the rule structure. During the solve episode itself I kept the generator, Racket authority, references, private labels, and prior solution material closed and used only `solve/challenge.json` plus my own local analyses. The required finish metadata should consequently record `earlier-exposure=yes` and `reference-consulted=no`.

## Revision 1 — repeated template rays

The three visible training inputs each contain one largest 8-connected nonzero object and smaller detached colored fragments. In each output, the large object's occupied-cell geometry is repeated outward in the direction indicated by each fragment, while each repeated copy takes that fragment's color. The fragment itself already occupies part of the first copy, so only missing zero cells visibly change.

The spacing is derived from the large object's bounding box: vertical translations use `bbox_height + 1`, horizontal translations use `bbox_width + 1`. A fragment's bounding-box center compared with the source center determines the signs of those translations, including diagonal rays. Repetition continues toward the canvas edge. Existing nonzero cells are preserved.

I implemented that hypothesis with 8-connectivity, doubled integer bounding-box centers, the largest component as the source template, and row-major component order as a deterministic tie/order convention. The main alternative considered was one-shot stamping at each marker; it is contradicted by the multiple farther copies visible in the training outputs. A fixed stride of four is also contradicted inside the visible set because the source bounding boxes include non-3-by-3 profiles.

Remaining uncertainty before the visible check: the examples do not strongly exercise collisions between rays of different colors or a tie for largest component. The implementation preserves the earliest existing/nonzero paint in row-major marker order and deterministically selects the first largest component.
