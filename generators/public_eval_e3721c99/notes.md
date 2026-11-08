# Topology-conditioned legend lookup — current design

Count enclosed four-connected background regions of each gray component, then
find the colored legend prototype with that many holes. Recolor the component
with the legend color; erase components with no exact match. Preserve the
legend and divider. Legend prototypes are non-gray components separated from
the canvas boundary; the separator may form a line or an L. Official test 1
contains two objects for which eight-connected background gives the wrong count.

The alternative `nearest_lower` treats legend hole counts as lower thresholds:
choose the greatest legend count not exceeding the object's count, or erase when
none exists. Inputs remain matched across settings. Both modes require topology
measurement followed by a scene-specific color lookup, not a fixed color code.

Plan: pin original labels and literal open/closed/diagonal cavity cases; author
Racket/Python topology implementations; sample varied holes, areas, contours,
legend keys/colors/order/orientation; audit rivals and shuffled public views;
run authoring preflight plus a wrong-hole-area causal witness. No owner approval
or training admission is claimed. Original source provenance is immutable.

Self-review repairs retained in tests: legend colors originally always decreased
with hole count, allowing a palette-order alias. The first two demos now teach
opposite palette orders and queries use unrestricted assignments. Production
sampling is self-contained in generator.py, with an isolated-file relocation test;
the native adapter reuses that core. The generated shapes include open exterior
pockets, variable cavity areas, and diagonal cavity/exterior contacts, so counting
bbox zeros, area, or eight-connected regions is wrong. The sampler rotates and
reflects the whole scene and varies legend membership, order and colors.
Finite audit: 32 seeds, 192 lessons, 9 declared rivals, no harmful survivors;
observed cavity counts 0..5 and individual cavity areas 1..5. No universal
uniqueness claim or owner acceptance is made. Ordinary gray objects may touch the
canvas boundary; colored legend prototypes remain interior and unambiguous.
