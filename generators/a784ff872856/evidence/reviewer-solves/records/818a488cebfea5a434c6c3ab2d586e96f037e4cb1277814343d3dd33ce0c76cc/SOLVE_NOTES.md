# Solve work log

## Exposure declaration before revision 1

Earlier rule exposure is **yes**. Before this post-repair episode was prepared, I had inspected the selected generator, canonical examples, and canonical Racket authority while repairing the task. After `solve prepare`, I did not reopen the generator, Racket rule, reference solution, private query labels, or prior solution explanations; this implementation uses only the displayed challenge plus my own Python.

## Revision 1 — crop, width-sort, and vertically pack

The visible examples contain three or four separated monochrome 4-connected objects. Each output preserves every object's pixels, translates each object to the top-left of its own bounding box, left-aligns those crops, and inserts one all-zero row between adjacent crops.

The ordering evidence is bounding-box width descending rather than occupied-cell count: in training examples 0 and 2, a sparse width-4 object with five cells appears before a dense width-2 object with six cells. The width-1 vertical object is last. I therefore extract same-color 4-connected components, normalize each crop, sort by width descending, and vertically pack with one-row gaps.

All displayed objects have distinct widths, so the examples do not identify tie behavior and the two queries do not need it. I used height descending and then color ascending as deterministic tie-breaks; that detail is consistent with my acknowledged earlier exposure, not independently established by the visible pairs.

No deliberately wrong revision was attempted. The first implementation was checked against all three visible training pairs.
