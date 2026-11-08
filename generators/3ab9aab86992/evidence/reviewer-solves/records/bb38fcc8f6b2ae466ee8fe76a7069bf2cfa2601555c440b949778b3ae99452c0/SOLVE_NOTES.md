# Solve work log

This is a human-authored visible-example solve. I had already read and repaired
the assigned generator before this phase, so earlier rule exposure is **yes**.
During this solve I did not reopen the generator, Racket source, reference
solutions, or private query labels. I used only the prepared visible examples.

## Revision 1

Hypothesis: the most frequent color is background. Every other 4-connected
object is a monochrome three-cell L inside a 2×2 box. The L's occupied corner
(top-left, top-right, bottom-left, or bottom-right) selects the same corner of
the output, independent of the object's input position and color. At that
output corner, draw an enlarged border L of the same color. For side length
`n`, each arm has `(n-1)/2` cells, so its union has `n-2` colored cells (5 for
7×7 and 7 for 9×9), matching the examples.

Checks from the visible data:

- In training example 0, the 8-object has the top-right occupied vertex and the
  output places 8 at the top-right; the 1-object maps to bottom-right.
- In training example 2, the 0-object maps to top-left and the 3-object maps to
  bottom-left despite both appearing near the top in the input, rejecting a
  position-based rule.
- Training example 1 contains all four orientations and confirms all four
  corner mappings, including color 0 as an ordinary object color.
- Test query 1 has two disconnected objects of the same color. They must be
  found by connected components rather than by treating a color as one object.

Implementation: find non-background same-color 4-connected components, normalize
each component to its 2×2 bounding box, classify the occupied vertex, and paint
the corresponding output-border L. Remaining cells stay background.

Remaining uncertainty: the visible examples are all odd square grids with valid
three-cell L objects. The solution intentionally targets that observed domain;
it does not define behavior for malformed components or rectangular canvases.
