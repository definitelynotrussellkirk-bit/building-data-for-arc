# Solve work log

## Prior exposure

Earlier rule exposure: **yes**. This solve follows generator repair work, so I already knew that the task family uses framed A:B::C geometric transfer. During this solve episode I consulted only `solve/challenge.json`; I did not open the Racket rule, generator implementation, reference solutions, private labels, or prior solve notes.

## Revision 1

The visible inputs are 6x20 arrays containing three color-5 frames. Their 4x4 interiors occupy rows 1–4 and columns 1–4, 8–11, and 15–18. I called those interiors A, B, and C.

Across the four visible training examples, B is a rigid square symmetry of A, and the labelled output is the same symmetry applied to C. I implemented all eight D4 symmetries, select the one that exactly maps A to B, and transfer it to C. This uses geometry rather than colors or sample position.

Potential ambiguity: a symmetric A could match more than one transform. The visible examples appear to make the intended mapping unique; the checker will test the complete visible set before I stop.
