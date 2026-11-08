# Solve work log

I had earlier rule exposure while reviewing this generator, so this is not a blind solve. During this solve I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, private labels, or prior solution explanations.

## Revision 1

The visible examples all contain a full monochrome non-7 row and a full monochrome non-7 column. I treated their intersection as the center of a horizontal/vertical reflection cross. Every non-7 cell that is off both axes is a source; its color is copied to its horizontal reflection, vertical reflection, and double reflection when each coordinate is in bounds. The original grid is retained, so the axes and source cells remain.

The examples also expose clipping and overwrite order. Reflections beyond an edge are omitted independently. Where different source orbits collide, the later source in row-major input order supplies the final color. The program therefore snapshots all sources from the original input and applies them row-major rather than discovering newly painted cells.

Potential alternatives rejected from the visible data: reflecting axis cells (would duplicate the cross), requiring all four reflected positions in bounds (contradicted by clipped examples), and unioning colors without overwrite order (contradicted by collisions).
