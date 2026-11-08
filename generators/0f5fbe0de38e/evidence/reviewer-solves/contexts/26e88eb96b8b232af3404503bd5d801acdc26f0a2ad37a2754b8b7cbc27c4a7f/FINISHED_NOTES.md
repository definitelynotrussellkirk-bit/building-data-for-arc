# Solve notes

Earlier rule exposure: yes, from reviewing this generator before the required post-repair solve. I did not consult the Racket source, generator source, private labels, reference solutions, or prior solution notes after `prepare`.

## Revision 1 hypothesis

The modal color is background. A single multicolor 3×3 component is a sparse template: its unique modal component color is the paint color and its other two cells are opposite-corner marker ports. External solid squares use the two marker colors. Pair different-colored squares greedily by nearest bounding-box gap. Each pair anchors a scaled D4 copy of the 3×3 template; retain the marker squares and paint the transformed/scaled template-fill cells.

The implementation recovers components and the template directly from the visible grid, tries D4 transforms in deterministic order, and supports one or more square scales and marker pairs.
