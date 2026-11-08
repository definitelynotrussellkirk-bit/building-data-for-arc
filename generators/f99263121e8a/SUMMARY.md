# f99263121e8a — crop and stack monochromatic components

Version **4.2.0**. Background is zero. Extract monochromatic **4-connected**
components, sort by `(leftmost column, topmost row)`, crop each **raw input
bounding box**, and stack those rectangles vertically with exactly one blank
row between them. Center each crop using floor division for left padding.
A crop can contain pixels belonging to another component. Color is not object
identity; equal left edges and different-colored contact are lawful.

Default generation uses the rotating five-example cycle
`order_conflict → crop_overlap → canonical → wide_narrow → diagonal_contact`.
The `order_conflict` and `canonical` profiles are canonical-like 10×10,
three-object anchors. The other three profiles deliberately expose raw-crop,
same-left tie, floor-centering, right-edge, color-grouping, touching-color,
and 4-vs-8-connectivity distinctions. Any five consecutive default examples at
a fixed seed and difficulty include the complete cycle. The task-local
adversarial scanner currently falsifies fourteen declared rival rules on every
such five-example window. A second finite search enumerates 503 cross-axis
alternatives and found none that fit a complete five-demo window in its retained
30-seed × 3-band run. Neither library proves unique inference or model
performance. Request **at least five demonstrations** when this
teaching guarantee matters.

General examples use 2–3/3–5/4–6 components for easy/medium/hard; the two
canonical-like anchors remain at three components in every band unless an
explicit component-count override is supplied. Explicit controls are
`grid_h=8..30`, `grid_w=9..30`, `n_components=2..6`, and
`texture=canonical|order_conflict|scattered|crop_overlap|shared_color|wide_narrow|equal_leftmosts|diagonal_contact`.
Previous unimplemented palette/density/position controls raise `ValueError`;
this is an intentional override-contract cleanup. Input and stacked output both
remain within 30×30. Placement fails explicitly rather than returning a partial
scene.

Production labels continue to come from the **unchanged canonical Racket**.
`rule_mirror`, semantic rivals, and workspace scanners are diagnostic hooks only.
Current verification is retained in the review return under `checks/`;
acceptance remains a maintainer decision, not an automatic consequence of
reviewer checks.
