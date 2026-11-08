# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observations and hypothesis

I had not seen this task's rule, generator, private answers, prior solution, or notes before preparation. I used only the visible examples printed by `review.py blind prepare`.

Each input contains one padded rectangular figure. The tight bounding box of all nonzero cells has even height and width and is mirrored across both its horizontal and vertical midlines. The output is exactly the upper-left quarter of that tight bounding box:

- examples 0--2: an 8x8 box becomes its upper-left 4x4 block;
- example 3: a 6x10 box becomes its upper-left 3x5 block;
- example 4: a 10x6 box becomes its upper-left 5x3 block.

This explains output zeros at the quadrant boundary: they are retained data, not padding to remove. I considered returning the smallest repeated tile, but the non-square examples specifically support "crop the upper-left half on both axes" rather than a fixed 4x4 tile.

## Probe and implementation

Before implementation I loaded train example 0 and called the untouched template; it failed with `NotImplementedError`, as expected. I then implemented: locate the nonzero bounding box, take its top half and left half, and preserve every cell in that rectangle. I included an empty-grid fallback returning `[]`, although no visible case is empty.

Visible-query predictions from this rule are:

- query 0: `[[6, 7, 0], [7, 0, 6], [0, 6, 7]]`;
- query 1: `[[0, 5, 0, 7], [8, 5, 5, 0], [7, 8, 0, 8], [7, 0, 3, 0]]`.

Remaining uncertainty: the examples strongly establish the upper-left quadrant, but they do not show an odd-sized tight box or multiple disconnected bounding boxes. The implementation follows the observed even-sized single-figure domain.
