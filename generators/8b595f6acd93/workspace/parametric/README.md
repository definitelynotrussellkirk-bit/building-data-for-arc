# Plus completion with updated-state pair classification

This proposed native family preserves the exact canonical default and adds one
non-collapsing composed setting.

| `mode` | Rule |
| --- | --- |
| `canonical` | Fill every zero center with four cardinal green (`3`) arms using yellow (`4`). |
| `pair_recolor` | Run canonical completion, then recolor every exact eight-connected yellow component of size two to azure (`8`). |

The sampler constructively includes a hollow plus whose newly filled center is
diagonally adjacent to one yellow seed. Stage A therefore creates an exact
8-connected pair; Stage B consumes that intermediate component. Other motifs
include unseeded pluses, two-seed trimers, incomplete/mismatched near-misses and
palette distractors. The 30×30 query contains motifs throughout the canvas.

Counts are independent (`demos` 2–6, `queries` 1–4), inputs are setting
independent, and shorter requests are prefixes of longer requests. Qualification
uses three demonstrations and four queries. Labels are checked through protected
Racket by the native worker. This is authoring evidence only, not owner
acceptance or training admission.
