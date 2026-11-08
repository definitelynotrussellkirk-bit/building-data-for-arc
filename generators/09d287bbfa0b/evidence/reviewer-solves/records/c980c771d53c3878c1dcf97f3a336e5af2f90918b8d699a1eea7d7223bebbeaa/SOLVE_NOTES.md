# Solve work log

I had earlier rule exposure while reviewing this generator, so this is not a blind solve. During this solve I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, private labels, or prior solution explanations.

## Revision 1

The visible examples all contain a full monochrome non-7 row and a full monochrome non-7 column. I treated their intersection as the center of a horizontal/vertical reflection cross. Every non-7 cell that is off both axes is a source; its color is copied to its horizontal reflection, vertical reflection, and double reflection when each coordinate is in bounds. The original grid is retained, so the axes and source cells remain.

The examples also expose clipping and overwrite order. Reflections beyond an edge are omitted independently. Where different source orbits collide, the later source in row-major input order supplies the final color. The program therefore snapshots all sources from the original input and applies them row-major rather than discovering newly painted cells.

Potential alternatives rejected from the visible data: reflecting axis cells (would duplicate the cross), requiring all four reflected positions in bounds (contradicted by clipped examples), and unioning colors without overwrite order (contradicted by collisions).

## Revision 2 after visible failure

Revision 1 executed correctly on training examples 0 and 2 but raised `StopIteration` on example 1. I traced this to an over-strong axis detector: the full horizontal row in example 1 contains no background 7 cells but is not monochrome because one position has color 1. The output leaves that full row unchanged, showing that the decisive axis property is complete non-background occupancy, not one color. I removed only the monochrome condition for both axes. The reflection, clipping, source snapshot, and overwrite hypotheses remain unchanged.

## Revision 3 after exact-grid comparison

Revision 2 removed the execution error, but training example 1 still differed at one cell: the orbit containing input colors 1 at `(1,5)` and 0 at `(3,5)` must finish as 0 at the first position and 1 at the second. Painting the source position itself collapses both cells to one last-write color. The visible output instead shows that each source paints only its three *other* reflected positions; its own coordinate is retained unless another source reflects into it. I changed the target list to horizontal, vertical, and double reflections only, excluding the identity target. This explains the observed color swap and preserves isolated sources naturally.
