# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, private labels, reference
solution, prior solve notes, or audit evidence. I used only the visible examples
printed by `review.py blind prepare`, `challenge.json`, and local Python checks.

## Revision 1 hypothesis

Each non-background color occurs a perfect-square number of times: 1, 4, 9,
or 16 in the visible episodes. The output discards the input geometry and turns
each such color into a solid square whose side is the square root of its count.
The most frequent color is the background. The solid squares are sorted from
smallest to largest, bottom-aligned, and separated by exactly one background
column. Output height is the largest side and output width is the sum of sides
plus one separator per adjacent pair.

Evidence:

- Train 0: counts 1/9/16 become 1x1, 3x3, 4x4 at columns 0, 2-4,
  and 6-9 in a 4x10 output.
- Train 1: counts 4/9 become 2x2 and 3x3 with one separating column.
- Train 2 repeats the 1/9/16 layout with different colors and input geometry.

I first ran `python3 test_visible.py` against the packet's untouched stub and
observed the expected `NotImplementedError`, establishing a failing visible
example check. I then implemented only this count-to-square packing rule.

Remaining uncertainty: no visible episode has two object colors with equal
perfect-square counts. The implementation uses color as a deterministic tie
breaker, but the examples do not establish a semantic order for equal sizes.
