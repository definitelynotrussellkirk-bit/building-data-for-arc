# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: I had not opened this task's generator, canonical rule, private labels,
reference solution, prior solve notes, or audit evidence. I used only the visible examples
printed by `review.py blind prepare` and the visible solve files.

Hypothesis: for each of colors 1, 2, and 3, count its 4-neighbor connected components.
The output has one row per color, filled from the left with that color once per component;
all rows are padded with zero to the largest component count. The extra color (8, 5, 7,
or 6 in the visible grids) is a distractor and is not summarized.

Evidence from the demonstrations:
- Example 0 has component counts (1, 4, 1), including diagonal-only separations for color 2.
- Example 1 has component counts (4, 2, 2).
- Example 2 has component counts (1, 2, 5), again requiring 4-connectivity rather than
  diagonal connectivity.
These exactly match the three output rows and their widths.

Alternatives rejected: total colored-cell counts do not match the output lengths; treating
diagonal contacts as connected would merge several color-2/color-3 objects and fail examples
0 and 2; counting the distractor color does not explain any output row.

For the two visible queries I manually predict component counts (5, 4, 5) and (2, 4, 3),
so the inferred outputs would have widths 5 and 4 respectively. I implemented a generic
flood-fill over the rectangular grid and have not used masked-query feedback.
