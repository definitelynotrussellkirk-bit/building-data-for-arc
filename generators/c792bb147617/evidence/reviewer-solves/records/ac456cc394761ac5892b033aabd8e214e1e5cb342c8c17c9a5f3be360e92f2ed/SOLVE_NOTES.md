# Post-repair visible-only solve notes

## Observation

All three visible input/output pairs preserve the grid shape and original blue
(1) cells. Around every original blue anchor, the output assigns a consistent
color by relative direction:

- above: 2
- left: 7
- right: 6
- below: 8

Writes are clipped at the grid boundary. For example, the top-left blue in
training example 1 has only right=6 and below=8; no out-of-bounds cells are
invented. The examples with eight anchors show the operation applies to every
anchor rather than a fixed small count.

## Hypothesis and implementation

Copy the input. Scan only the original input in row-major order. For each cell
whose original value is 1, write the four in-bounds directional colors into the
copy, leaving all other cells unchanged. Reading anchors from the immutable
source avoids mistaking newly written colors for anchors.

## Exposure declaration

This is an exposed post-repair solve: I had seen the task rule earlier while
repairing the generator. During this solve episode I used only the visible
presentation produced by `review.py solve prepare` and did not reopen the rule,
generator, solution records, or private labels.
