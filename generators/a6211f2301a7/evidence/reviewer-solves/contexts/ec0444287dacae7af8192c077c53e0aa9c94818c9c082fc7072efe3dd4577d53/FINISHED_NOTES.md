# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit records, or earlier solution notes. I used only the visible
examples printed by `python3 review.py blind prepare`.

## Revision 1 — crop, then rotate clockwise

Each training input contains a single sparse nonzero object embedded in a larger
zero background. Cropping to the smallest rectangle containing every nonzero
cell gives:

- example 0: `[[4,0,3],[5,0,0]]`;
- example 1: `[[8,1],[1,8],[8,1]]`;
- example 2: `[[7,2,0],[7,0,5]]`.

Rotating each crop 90 degrees clockwise exactly produces its visible output.
This explains both output dimensions and all retained zero cells inside the
bounding box; simply transposing or rotating the whole input would not.

I implemented the rule without NumPy: find nonzero coordinates, crop their
bounding box, reverse the rows, and transpose. For an all-zero input I return an
empty grid, although no visible example exercises that case.

Predicted query outputs before checking:

- query 0: `[[6,9,0,9],[9,9,0,3]]`;
- query 1: `[[2,2,2],[0,0,0],[2,0,0]]`.

Remaining uncertainty is limited to the unshown all-zero convention and whether
zero is always the background; both are strongly implied by all visible cases.
