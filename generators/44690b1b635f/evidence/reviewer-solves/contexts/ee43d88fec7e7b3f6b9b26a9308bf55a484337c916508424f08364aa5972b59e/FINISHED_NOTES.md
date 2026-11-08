# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private labels,
or earlier solution notes before preparing the blind episode. I had only read the packet
instructions and assignment duties.

## Revision 1 — connected checkerboard fill

The examples contain fixed colour-8 walls and a small two-colour marker embedded in one
open component. The output leaves walls and disconnected chambers unchanged, while every
cell in the marker's component becomes a checkerboard using the two marker colours. The
colour appearing once is the phase anchor; cells with the same row+column parity as that
anchor receive its colour, and opposite-parity cells receive the companion colour.

I checked this interpretation manually against all three examples: the simple vertical
partition fills only the left chamber, and the two mazes fill exactly the open component
reachable from the one-cell anchor. The second query also contains a remote companion-colour
cell; its parity agrees with the inferred checkerboard and the wall gaps connect all three
vertical regions. The implementation therefore flood-fills non-8 cells from the unique
anchor and paints that component by parity.

Remaining uncertainty: the visible data strongly identifies colour 8 as the wall and colour
0 as unpainted space, so the code intentionally binds to those task-specific roles rather
than attempting a generic palette inference.
