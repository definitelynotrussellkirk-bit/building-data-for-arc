# Solve notes

## Revision 1 — connected components, not aggregate color frequency

From the visible pairs, each output is the tight bounding box of one non-zero,
monochromatic, 4-connected component. The selected component has the greatest
cell count among components, and zeros inside its bounding box are retained.

The examples deliberately separate aggregate color count from component size:
for example, train 0 has eight cells of color 2 split into two 2x2 components,
while the seven-cell color-5 component is selected. Train 3 similarly has six
color-8 cells split into two triominoes while the connected color-6 component is
selected. This rules out “most frequent color” and supports “largest connected
component.”

Implementation: enumerate same-color 4-neighbor components, require a unique
largest component, and slice the original grid to that component's bounding box.
I did not consult a rule or reference while solving. I had earlier exposure to
the task semantics during the generator review, which will be recorded honestly
at finish.
