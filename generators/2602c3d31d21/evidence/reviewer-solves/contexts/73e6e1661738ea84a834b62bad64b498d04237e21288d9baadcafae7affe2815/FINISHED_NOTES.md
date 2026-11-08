# Solve work log

## Exposure before solving

I had not opened task `2602c3d31d21`'s generator, canonical rule, private labels,
reference solution, prior solve, or audit material. Before preparation I had read
packet-level instructions and listed repository directories; I did not inspect this
task's implementation or rule.

## Hypothesis and probes

The rightmost column is a key: its nonzero cells list the object colors in table
order. Each listed color also forms one disconnected shape in the remaining
columns. The output is a square comparison table rendered as 2x2 colored blocks
with one zero row/column between blocks. The first row and column reproduce the
key. An off-diagonal table entry is color 2 when the two source shapes are the
same free polyomino under translation, rotation, or reflection, and color 5
otherwise; the diagonal is zero.

I extracted each visible object's normalized occupied coordinates and compared
all eight square-grid symmetries. This exactly reproduced every relation in all
three training outputs, including identical shapes, rotated T-like shapes, and
mirror-only matches. A local visible-example regression test failed against the
initial `NotImplementedError`, then passed for all three examples after the
implementation.

## Remaining uncertainty

The solution assumes the generator reserves the last input column for the key
and places every compared object strictly before that column, as all visible
examples do. It also assumes key colors are unique. No hidden labels or reference
implementation were consulted.
