# Solve work log

## Prior exposure

Before this visible-only episode was prepared, I had already reviewed the selected generator and canonical rule as part of the assigned repair. I therefore will finish with `earlier-exposure=yes`. During this solve episode I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solve explanations.

## Revision 1 — connected figure, marker vote, corner triangle

From the six visible examples I separated the uniquely largest 8-connected nonzero component from the remaining colored cells. The output preserves that large figure and erases the remaining cells. Those erased cells act as markers: their most frequent color becomes the fill color. Examples 1, 4, and 5 show frequency ties; the winning tied color is the one whose first marker occurs earliest in row-major order, not the numerically smallest or largest color.

Exactly one marker lies at a grid corner. It anchors a right isosceles triangle pointing into the grid. With `K` marker cells, the visible triangle has side length `K-1`: for example six markers produce 15 filled cells (side five), and five markers produce 10 (side four). The triangle is painted after preserving the main figure, so it overwrites any overlap. I implemented those observations directly and planned one ordinary `solve` check; no deliberately wrong revision was manufactured.

Remaining uncertainty before checking: the public examples all have a unique largest component and a unique marker corner, so the solution intentionally follows that observed contract rather than inventing behavior for ambiguous inputs.
