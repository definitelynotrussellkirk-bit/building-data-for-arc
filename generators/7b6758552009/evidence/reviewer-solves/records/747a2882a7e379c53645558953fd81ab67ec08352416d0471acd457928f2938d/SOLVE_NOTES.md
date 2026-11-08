# Solve work log

## Exposure declaration before solving

I had not opened task `7b6758552009`'s generator, Racket rule, notes, private
labels, reference solution, or any prior explanation. I used only the generated
`challenge.json` and this task's solve README/template.

## Revision 1 — left-to-right object ordering

The inputs contain several separated nonzero monochrome objects, while each
output is a one-row sequence of colors. I compared candidate orderings:

- Raster order fails training example 2: the singleton 9 appears on the same
  early row as 7 but is output after the lower 4.
- Descending object size fits examples 1–3 but fails example 4, whose three-cell
  objects would not yield `5,1,5,1` under any simple raster tie-break.
- Sorting connected objects by their leftmost column fits all four examples.
  In example 4, the objects' left edges are at columns 0 (5), 3 (1), 6 (5),
  and 9 (1), exactly matching the output. Example 1 has two objects tied at
  column 0, and their top-to-bottom order matches `4,2`.

I implemented 4-connected, same-color component extraction, discarded background
0, and sorted by `(leftmost column, topmost row)`. Each component contributes its
color once. This predicts the two hidden-query outputs structurally as five and
four colors respectively, without consulting their labels.

Remaining uncertainty: the visible examples do not distinguish left edge from a
horizontal center coordinate when objects do not overlap in x, except that the
left-edge rule is the simplest ARC-style reading-order interpretation. They also
do not expose diagonal-only connectivity; 4-connectivity is the conservative
object convention for these rectilinear shapes.
