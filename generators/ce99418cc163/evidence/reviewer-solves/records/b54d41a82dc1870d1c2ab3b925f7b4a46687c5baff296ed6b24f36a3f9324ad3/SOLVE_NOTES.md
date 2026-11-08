# Blind solve notes — `ce99418cc163`

This is a human work log based only on `solve-blind/challenge.json`. I did not
open the generator, canonical rule, reference solutions, private labels, audit
records, or the assigned repair target before finishing this episode.

## Observations

- The output preserves every input cell except for a few background (`0`) cells
  changed to green (`3`).
- Each changed cell is the fourth corner of an axis-aligned rectangle whose
  other three corners are red (`2`).
- Training example 3 is the minimal witness: red at `(1,1)`, `(1,8)`, and
  `(2,1)` causes green at `(2,8)`.
- Training example 2 contains two independent witnesses, including rectangles
  with adjacent rows and with rows separated by three cells, so the rule is not
  limited to a fixed size.
- Distractor colors are inert. In training example 1, `(9,10)` is color `1` and
  is also the fourth geometric corner of three red cells at `(8,0)`, `(8,10)`,
  and `(9,0)`; the output leaves it unchanged. Therefore only a blank fourth
  corner is filled, and other colors are not overwritten.

## Hypothesis

For every pair of distinct rows and columns, inspect the four rectangle corners
in the original grid. If exactly three corners are red (`2`) and the fourth is
background (`0`), color the fourth corner green (`3`). Use the original grid for
all detections so inserted green cells do not cascade.

## Probe

I enumerated all row-pair/column-pair rectangles with a short Python script and
reproduced all three visible training outputs exactly. It predicts these test
changes (zero-indexed):

- test 0: `(5,4)` and `(9,7)` become `3`; the yellow `4` at `(0,11)` remains.
- test 1: `(2,2)` and `(3,10)` become `3`.

No failed natural solve revision was needed; the first implemented hypothesis
fits every visible example and includes the occupied-corner counterexample.
