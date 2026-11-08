# Solve work log

I had earlier exposure to the family rule while reviewing the assigned generator,
so this is an exposed post-repair solve, not a blind solve.  During this solve I
used only the visible challenge presentation and did not reopen the generator,
canonical rule, reference solutions, private query labels, or prior solve notes.

## Revision 1

Visible examples show exactly four nonzero cells forming a solid 2x2 source.
Each source corner is copied into a 2x2 patch in the diagonally opposite region:
top-left goes down/right, top-right down/left, bottom-left up/right, and
bottom-right up/left.  The near corner of each target patch is two rows and two
columns beyond the source block boundary; cells outside the grid are simply
clipped.  Existing source cells are preserved.

I implemented that geometric rule directly, including structural validation and
clipped painting only into background cells.  The main alternative I considered
was anchoring patches to absolute grid corners, but train example 0 places the
right-side patches at columns 5 only while keeping the left patches at columns
1-2, which tracks the source offsets and clipping rather than fixed corners.
Remaining uncertainty is limited to whether unexpected malformed inputs exist;
the visible task manifold is unambiguous.
