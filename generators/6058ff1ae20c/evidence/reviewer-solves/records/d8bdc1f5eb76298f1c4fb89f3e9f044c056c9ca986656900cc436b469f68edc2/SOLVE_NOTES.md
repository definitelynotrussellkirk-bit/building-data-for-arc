# Solve work log

## Exposure declaration

Before this post-repair solve I had already inspected the assigned generator and
canonical Racket source as part of the required repair. This is therefore an
**exposed** solve, not a blind result. After `solve_episode.py prepare`, I used
only `solve/challenge.json`, this solution file, and solve-check feedback; I did
not reopen the generator, rule, references, private labels, or earlier solution
explanations.

## Revision 1

Visible-example hypothesis:

- Every non-zero input cell is a seed.
- A seed's color fills the complete row and complete column through that seed on
  an otherwise zero output grid.
- With two seeds of the same color, both crosses are unioned.
- The distinct-color example reveals precedence: seeds are handled top-to-bottom
  / row-major, and the later seed overwrites both intersections with earlier
  crosses. Its seed at row 3, color 2, owns both crossings with the row-2 color-9
  cross.

Implementation: scan non-zero cells in row-major order, begin with a fresh zero
grid, and for each seed paint its column followed by its row. This also handles
one seed and same-color pairs without special cases.

Remaining uncertainty before check: none about the visible examples; masked
queries could still expose an unshown arrangement, but the rule inferred here is
the simplest uniform explanation of all three demonstrations.
