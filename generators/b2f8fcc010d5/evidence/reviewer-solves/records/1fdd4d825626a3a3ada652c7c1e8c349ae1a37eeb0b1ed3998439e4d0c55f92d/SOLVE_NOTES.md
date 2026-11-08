# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — parity-lattice subsampling

The nonzero cells largely occupy checkerboard-parity coordinates, and the target is
3×3, so I first tested the simplest compression: retain rows and columns 0, 2, 4.
This preserves all four corners and the center. I expect the visible examples to
show whether the four edge cells instead come from the interior odd/odd positions.
No generator, rule, private label, or prior solution material has been opened.

## Attempt 2 — untwist the four interior quadrant cells

Attempt 1 failed all three examples. Comparing each target position across all
examples gives a consistent geometric mapping: preserve the four outer corners and
the center; move (1,1) to top-middle, (1,3) to middle-left, (3,1) to middle-right,
and (3,3) to bottom-middle. The even/even edge-midpoint cells are distractors. This
is an untwisting of the four odd/odd quadrant cells around the fixed center/corners.

Predicted queries:

- query 0: `[[5,5,5],[5,3,6],[8,4,1]]`
- query 1: `[[5,5,5],[5,8,9],[3,2,7]]`
