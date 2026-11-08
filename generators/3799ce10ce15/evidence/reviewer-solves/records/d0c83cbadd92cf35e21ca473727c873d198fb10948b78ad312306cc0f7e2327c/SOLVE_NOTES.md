# Solve work log

## Exposure declaration before solving

I had already studied this task's generator and canonical transformation while repairing it, so this is **not a blind rule-discovery record**. During this solve episode I used only `solve/challenge.json` and my own Python; I did not reopen the generator, Racket source, private labels, or earlier solution explanations.

## Revision 1 — ordered legend × ordered frame presence

Visible evidence: the nonzero non-9 cells in row 0 form an ordered legend. The body contains separate hollow rectangular components of color 9. Each visible output has one row per frame in top-left scan order and one column per legend entry. An output cell repeats the legend color exactly when that color occurs anywhere in the corresponding frame interior; multiplicity and exact position inside the frame do not matter.

Implementation: find 4-connected color-9 components, retain only components equal to a complete rectangular border, sort their bounding boxes by top-left position, and emit the frame-by-legend presence matrix. This also handles different frame sizes, positions, frame counts, legend lengths, and repeated interior cells shown in the examples.

Alternative rejected from the visible examples: fixed canonical frame windows cannot explain the moved, resized, vertically arranged, and four-frame examples. Counting occurrences also fails because repeated cells still produce one legend-colored output cell.

Remaining uncertainty before checking: whether frames are ordered row-major by top-left corner or by some other object enumeration. The visible examples with vertically and horizontally separated frames support row-major top-left order.
