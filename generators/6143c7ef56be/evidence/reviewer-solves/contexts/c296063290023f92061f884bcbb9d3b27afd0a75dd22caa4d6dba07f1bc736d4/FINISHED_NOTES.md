# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, private answers, prior solves,
or audit evidence. I used only the visible examples printed by `review.py blind
prepare` and `challenge.json`.

## Revision 1 — quadrant markers fill the gray block

Hypothesis: the four nonzero singleton colors are quadrant labels around the gray
2×2 block. The output clears the canvas and gray cells, then places the
upper-left, upper-right, lower-left, and lower-right marker colors into the
corresponding cells of that block.

Evidence from the visible examples:

- Example 1 has the four colors at the canvas corners and copies them into the
  gray square in corner order.
- Example 2 does the same with a different shape and palette.
- Example 0 is the stronger probe because the markers are not at canvas corners;
  their positions relative to the gray block still predict `[[9,4],[3,6]]`.

Implementation: locate the exact gray 2×2 rectangle, classify every other
nonzero cell by whether it lies above/below and left/right of the block center,
create an all-zero output of the original shape, and write the four colors into
that rectangle. Remaining uncertainty is limited to unseen malformed inputs or
markers lying exactly on a block centerline; neither occurs in the visible task
family.
