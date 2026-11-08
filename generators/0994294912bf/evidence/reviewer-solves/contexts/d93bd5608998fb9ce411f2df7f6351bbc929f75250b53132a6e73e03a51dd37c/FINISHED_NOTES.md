# Solve work log

## Prior exposure

This is a post-repair visible-example solve, not a clean blind solve. Earlier in the
review I had already inspected and tested the intended transformation while repairing
the generator. I did **not** reopen the generator, Racket rule, reference outputs, or
private labels during this solve episode. I therefore record `earlier-exposure yes`
and `reference-consulted no`.

## Revision 1

From the visible examples I identified a full row and column of color 9 dividing the
grid into four quadrants. The worked top pair shows a solid object becoming its
four-neighbor boundary in the corresponding position. The query bottom-left may use
several colors, but its first nonzero cell in row-major order supplies the single
output color. I therefore:

1. locate the all-9 separator row and column;
2. take the union of nonzero cells in the bottom-left quadrant;
3. retain cells with at least one missing orthogonal neighbor;
4. translate those local coordinates into the bottom-right quadrant;
5. paint them with the first bottom-left nonzero color, preserving other cells and
   clipping translated cells that fall outside the grid.

I considered preserving each source cell's color, using the modal color, and refusing
to overwrite occupied target cells. The multicolor and prefilled-target examples make
those alternatives inconsistent with the visible outputs, so the program uses one
row-major color and overwrites only derived outline positions.

Command/probe: `python3 solve_episode.py check --intent solve ...`.
Remaining uncertainty before the check: only whether the boundary is cardinal rather
than diagonal; the solid-rectangle examples support the cardinal interpretation.
