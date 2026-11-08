# e3f72a0f2ebb

Replace every same-color, 4-connected nonzero component with the frame of its
tight bounding box on a fresh zero grid. The Racket reference is unchanged.

Version 4.0.0 generates exactly 2–4 objects, with 1–4 distinct colors, on 7–18 by
8–18 grids. Whole output rectangles are reserved during placement. Disconnected
objects may share colors; singletons, lines and complete frames are valid fixed
points. Every ordinary draw requires both completing borders and erasing an
interior, and a four-phase teaching schedule supplies repeated-color and
unchanged-component witnesses. Four demonstrations are requested per lesson.

Exact controls: grid_h, grid_w, n_blobs, n_distinct_colors. All are observable
from returned pixels. More distinct colors than objects is explicitly invalid;
unknown or retired controls are rejected. Difficulty changes default sampling
weights while preserving the full exact-control domain and canonical-scale
support in every band. Larger unpartitionable and overlapping-box arrangements
are outside the generated domain; this is not an exhaustive Racket-domain sampler.

Approval remains derived from accepted source-bound review evidence.
