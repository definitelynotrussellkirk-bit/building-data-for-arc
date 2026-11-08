# 021fb6acf24f — ordered bounding-box fills

Selected generator version: **3.0.0**. A zero-background grid contains one or
two nonzero colors, with exactly two anchors per color in distinct rows and
distinct columns. The canonical Racket runtime's `unique` primitive sorts numeric
values, so colors are processed in **ascending numeric order**. Each color fills
only cells that are still zero inside its anchor bounding box; the lower color
therefore owns contested overlap cells.

The default sampler cycles five exact canonical profiles: 10×10/one color,
7×8/two colors, 9×8/two colors, 10×10/two colors, and 6×11/one color. Two-color
draws deliberately place the larger color first in raster scan order and create
background overlap cells, refuting both scan-order and late-overwrite shortcuts.
Difficulty changes rectangle geometry without changing the profile schedule.

Public controls are only `grid_h` (6..10), `grid_w` (8..11), and `n_colors`
(1..2). They are exact, observable, legal in every difficulty band, and reject
unknown or malformed overrides. Every generated output retains some background.

Canonical Racket source was not changed. The selected base target's normalized
`target_code` was synchronized to the canonical `program_solution`; historical
`raw_code` remains intact. The final source-bound battery is 12/12 green and a
300-lesson census found no ambiguity against the three declared competitors in
production or any of 1,200 held-out-query rotations. This is finite-rival
evidence, not a proof of unique induction or training admission.
