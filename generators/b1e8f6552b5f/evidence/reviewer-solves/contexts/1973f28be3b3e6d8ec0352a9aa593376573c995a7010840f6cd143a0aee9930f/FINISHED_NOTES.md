# Solve work log

## Exposure declaration before solving

This is the required post-repair, exposed solve. Before `solve_episode.py
prepare`, I had reviewed this task's generator and canonical Racket rule while
repairing the distribution, so earlier rule exposure is **yes**. After preparing
this episode I did not reopen the generator, rule, private labels, reference
solutions, or prior solution explanations; the implementation below was checked
only against the visible challenge.

## Revision 1 — hollow 3x3 ring per marker

Across all four demonstrations, each isolated nonzero input cell disappears from
its original center and contributes its own color to the eight neighboring cells
of a 3x3 square. The output starts from an all-zero canvas rather than retaining
the input: this matters because every original center is zero in the output.
Markers near an edge still produce the complete ring because the visible inputs
place them one cell inside the canvas. Multiple markers are handled independently,
including repeated colors and four-marker examples.

I rejected a solid 3x3 stamp because every output center is empty, and rejected a
plus/corners-only stamp because each example contains both orthogonal and diagonal
ring cells. Remaining uncertainty is limited to overlapping footprints; none of
the visible demonstrations overlap, so the straightforward row-major overwrite
behavior is used if such an out-of-distribution input appears.
