# Solve work log

## Exposure statement

Before this visible-only solve I had read only the packet-level instructions and the assignment text. I had not opened this task's generator, Racket rule, reference solution, private labels, audit evidence, or earlier solve notes.

## Revision 1 — mirrored exact-match filter

The input is split by a full-height nonzero vertical divider. The two sides have equal width. Comparing each right-hand cell with the cell at the same row and equal distance on the left explains every retained output cell:

- an equal nonzero color pair is retained at the right-hand position;
- a mismatch, a one-sided mark, the left copy, and the divider are erased;
- the output keeps the original canvas size.

I checked this manually against all five demonstrations. For example, in training example 0, left `(1,2)=7` mirrors right `(1,8)=7` and survives, while left `(3,1)=2` mirrors right `(3,9)=4` and is erased. Training examples 2–4 also require color equality rather than occupancy-only overlap.

Implementation: locate the unique solid nonzero divider column, initialize an all-zero grid, and copy each nonzero cell on the right only when its reflected left counterpart has the same value. Remaining uncertainty is limited to whether an unseen episode could place the desired matches on the left instead; all visible outputs consistently select the right side, so the implementation follows that evidence.
