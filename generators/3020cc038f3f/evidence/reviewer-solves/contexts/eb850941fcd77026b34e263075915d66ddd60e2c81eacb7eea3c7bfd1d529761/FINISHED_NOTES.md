# Solve work log

I had not opened the generator, Racket rule, reference solutions, private labels,
or earlier solution explanations for task `3020cc038f3f`. Before this blind solve I
had only read the packet-level instructions and the generated visible challenge.

## Revision 1 — Boolean combination of normalized silhouettes

The grids contain a singleton marker at the upper-left (colors 3, 4, or 5), one
object in color 1, and one object in color 2. I extracted each object's tight
bounding-box silhouette and aligned the two silhouettes at their upper-left
corners, padding the smaller one with empty cells.

Visible-example probes:

- Marker 4, example 1: the two silhouettes are identical. XOR gives no occupied
  cells, matching the `[[0]]` output.
- Marker 4, example 2: upper-left-aligned XOR exactly yields the five gray cells
  in the 3x3 output. Alternative placements (centering or lower/right alignment)
  do not match.
- Marker 3, example 3: upper-left-aligned OR exactly fills the one cell missing
  from the color-2 silhouette, matching the seven gray output cells.

This suggests marker 3 = OR, marker 4 = XOR, and the unseen marker 5 = AND. The
output recolors occupied cells to 8 and crops to the tight nonzero bounding box;
an empty result is represented by `[[0]]`. Cropping is needed to explain why the
all-zero XOR is 1x1 rather than the original 3x3 canvas.

Remaining uncertainty: marker 5 is inferred from the natural three-operation
family rather than demonstrated directly in the training examples. The second
query is therefore the key extrapolation. I implemented only this compact rule.
