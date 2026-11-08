# Solve work log

## Earlier exposure

Before this visible-only solve I opened only packet-level instructions and the generated public challenge. I did not inspect this task's generator, rule, private labels, prior solutions, notes, or audit evidence.

## Revision 1 — translate the color-1 stencil from anchor 2 to anchor 3

The four color-1 cells form a stencil around the single color-2 anchor. The single color-3 cell is a destination anchor. In every training pair, the output paints color 8 at exactly the same relative offsets from color 3 that the color-1 cells occupy relative to color 2. Existing cells at those destinations are overwritten by 8; all other cells remain unchanged.

Concrete checks:

- Example 0: relative to 2 at `(7,2)`, the 1 offsets are `(-1,-1), (-1,0), (0,-2), (0,-1)`. Applied to 3 at `(8,3)`, these become `(7,2), (7,3), (8,1), (8,2)`, exactly the four output 8s.
- Example 1: offsets `(0,-1), (1,-1), (1,0), (1,1)` from 2 at `(11,1)` become the four output 8s around 3 at `(6,4)`.
- Example 2: offsets `(-1,-2), (-1,-1), (-1,0), (0,-1)` from 2 at `(3,8)` become the output 8s around 3 at `(8,7)`.

The implementation copies the input, finds all color-1 cells and the singleton anchors 2 and 3, translates each stencil offset, and paints 8. The visible examples do not show out-of-bounds translated offsets; the implementation defensively skips them rather than changing output dimensions.
