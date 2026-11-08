# 531e65dffc0a — anchor-coded rotation stamps

One monochrome connected prototype supplies the shape and output color. Isolated
anchors encode rotations: 2 = identity, 3 = clockwise 90 degrees, 4 = 180 degrees,
5 = counter-clockwise 90 degrees. Each anchor locates the transformed bounding-box
origin, which can itself be an empty cell. The unchanged Racket rule paints onto
a fresh same-size background, clips individual out-of-bounds pixels, and takes the
union of same-color overlaps. A stamp crossing the original prototype footprint
is retained; source cells are not erased in a postprocessing step.

Selected generator version: **2.1.0**. Rule pin: **4acd30f1e03a**.

Default even sample indices produce four-code teaching scenes that distinguish
six canonical-fitting shortcuts and twelve single-code mapping errors. Default
odd indices mix ordinary canonical-size/palette profiles (75%) with broad scenes
(25%), including symmetric prototypes. Explicit non-null overrides select broad
sampling and honor all requested values; no teaching guarantee is claimed for
arbitrary override-defined lessons.

The sampled domain has one monochrome 4-connected prototype and isolated anchors.
The Racket rule's larger multiple-prototype/distractor domain is not covered.
Approval is derived by the catalog from exact source and review evidence; this
repair does not itself admit generated trajectories to training.
