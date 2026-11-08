# Solve work log

Earlier task-specific rule exposure before this blind solve: none. I had only read
packet-level instructions and the visible examples produced by `blind prepare`.
I did not inspect any generator, canonical rule, reference solution, private label,
or earlier explanation for task `297c05190f7c`.

## Revision 1 — iterative missing-corner completion

Hypothesis: for each nonzero color, any 2x2 window containing exactly three cells
of that color and one background cell is completed by coloring the missing corner.
Repeat to a fixed point, since a newly completed corner may create another such
window.

Evidence from the visible demonstrations:

- Train 0: the color-7 triomino is one three-corner 2x2 block.  The long color-8
  L border repeatedly completes adjacent 2x2 blocks and therefore fills its whole
  rectangular interior.
- Train 1: color 4 similarly propagates through its thin L-shaped border.  Color 9
  has only one qualifying window, so exactly one new cell appears.
- Train 2: every added 1, 3, or 8 is the sole missing corner of a monochromatic
  2x2 block; no unrelated background cells change.

Implementation details: collect all proposals from the current grid, apply only
unambiguous proposals simultaneously, and iterate until no update remains.
Existing colored cells are never overwritten.  Simultaneous rounds avoid scan-order
artifacts; a cell proposed by different colors is conservatively left unchanged.

Alternatives rejected: filling every colored component's bounding box is too broad
for the color-9 component in train 1.  A one-pass repair is too weak for the large
L-shaped rectangles in trains 0 and 1.

Remaining uncertainty: the examples contain no conflicting proposals from two
colors.  The implementation leaves such a cell unchanged rather than choosing an
arbitrary color.
