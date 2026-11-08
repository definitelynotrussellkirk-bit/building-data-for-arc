# 28c998e193d9 — Component-Wise Horizontal Closure

Version: `3.0.0`  
Canonical rule hash: `b18cc934f1d8`

## Input distribution

A canonical-scale `8x14` or `9x15` grid contains exactly two or three red (`2`) 4-connected outline components on black (`0`). Components may occupy the same rows, but a zero gap keeps them disconnected. Every generated grid contains one or two connected **bent** outlines whose horizontal span changes with height; the remaining components are open rectangular frames. Reflections vary orientation without changing the task vocabulary.

The single observable axis is `scene_profile`:

- `pair_one_bent`
- `triple_one_bent`
- `pair_two_bent`
- `triple_two_bent`

Each difficulty band cycles through all four profiles. Unknown or invalid overrides are rejected.

## Rule

Separate the red cells into 4-connected components. For each component independently, and for each row occupied by that component, paint cyan (`8`) from that row's leftmost component cell through its rightmost component cell. Union those component-wise row closures on an otherwise black output grid. Do not bridge different components merely because they share a row.

## Why this distribution

The imported generator emitted only disjoint open rectangles and incorrectly described the task as whole-bounding-box fill. Those examples could not distinguish the intended rule from “detect each frame and fill its rectangle.” Bent components make whole-bbox and frame-filling shortcuts disagree with the intended per-row closure, while shared rows with zero gaps refute global row bridging.
