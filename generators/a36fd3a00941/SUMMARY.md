# a36fd3a00941 — perimeter gallery

Generator version `3.0.0`; Racket authority hash `d0dcd1dd1256`.

A canonical-scale zero-background grid contains exactly three separated,
monochrome 4-connected components. For each component, crop its bounding box,
sort crops by bounding-box perimeter ascending with original left column and
then top row as tie-breaks, and pack the crops left-to-right, top-aligned, with
one zero column between adjacent crops.

The generator cycles deterministically through the canonical input profiles
`8x12`, `9x11`, `8x13`, and `9x12`. Every sample contains bboxes `2x2`, `3x2`,
and `1x5`, with perimeters `8,10,12`, areas `4,6,5`, and occupied counts
`4,5,5`. This makes the intended order disagree with the strongest
canonical-fitting shortcuts—ascending bbox area and ascending occupied-cell
count—on every generated example. Placement, color, crop sparsity, height, and
gaps also refute scan-order, color-order, descending-perimeter, solid-bbox,
bottom-alignment, and no-gap rivals.

The only advertised override is `scene_profile`; unknown overrides fail closed.
Difficulty alters nuisance placement but not the rule witness. Lessons use three
demonstrations and declare both ordered-production and query-rotation
identifiability checks against the named competitors.

Kind: `per_puzzle`. Imported version: `2.0.0`; repaired version: `3.0.0`.
Approval remains catalog-derived from current code and retained evidence.
