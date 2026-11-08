# Native component-rank family

`rank_metric=cells` is the exact canonical rule: find nonzero 4-connected
components, sort them by occupied cell count, and repaint ranks 2/3/4.
`rank_metric=bounding_box` keeps component discovery and repainting but ranks by
bounding-box area.

The two minimum demonstrations are a constructive teaching pair. Their component
shapes and placements force occupied-cell, box-area, density, scan-position,
input-color, perimeter, width, and height orderings to disagree in complementary
ways, so the supported finite shortcut set cannot explain both labels. Later
demonstrations and four private queries add randomized geometry and color; query
four is a substantive 30x30 edge-touching scene. The production generator and
canonical authority are unchanged.
