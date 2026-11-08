# Solve work log

Earlier exposure: none to task `0ab5dc1f5386`'s rule, generator, notes, solutions, or private labels. I had read only the packet-wide instructions and then `solve-blind/challenge.json`.

## Observations and hypotheses

The inputs contain hollow color-8 rectangles and smaller non-8 colored objects. A copied object preserves the full contents of its bounding box, including internal zeros, and only fits a frame when its bounding-box dimensions exactly equal the frame's interior dimensions; no rotation is used.

Simple size matching was insufficient. In training example 2, two 2x3 objects could fit the one 2x3 interior, but only the earlier object in reading order was copied. In training example 3, the first 2x2 frame is followed by a matching 2x2 object and is filled, while the second 2x2 frame appears after the other matching object and remains empty. This suggested an ordering rule rather than nearest-neighbor placement.

The resulting hypothesis is a row-major event scan: a hollow azure frame creates a pending slot; a later loose object fills the earliest pending frame with the same exact interior dimensions. An object encountered before a compatible frame is not saved for later. Each frame and object is used at most once.

## Implementation probe

I implemented 4-connected component detection, strict hollow-rectangle recognition for color 8, multi-color component detection for all nonzero/non-8 cells, row-major ordering by bounding-box top-left, and FIFO matching by exact dimensions. I then compared the program against all four visible training outputs locally before invoking the packet checker.

## Alternatives considered

- Pure size matching would incorrectly fill the later frame in training example 3 and leaves the duplicate-object choice in training example 2 unexplained.
- Nearest compatible object would choose the wrong 2x3 object in training example 2.
- Rotation/transposition is contradicted by the unmatched 3x2 object beside a 2x3 frame.
- A simple southwest-direction rule explains several examples, but the row-major pending-slot rule explains both duplicate cases with one mechanism and makes distinct predictions for both test inputs.

## Remaining uncertainty

The visible examples do not distinguish FIFO from LIFO if several same-sized frames are pending before several matching objects. FIFO is the conservative row-major interpretation. The implementation uses FIFO and never reuses an object.
