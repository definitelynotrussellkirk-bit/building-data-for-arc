# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Visible-only observations:

- Each input contains two or three rectangular frames made of color 1.
- Removing each frame leaves a small interior bitmap in another color.
- The demonstrated output is exactly the interior bitmap with the largest number
  of non-background colored cells: counts are 7 over 6/5, 8 over 6, and 7 over 5.
- Largest area and highest density are both contradicted by at least one example,
  so the selection criterion is colored-cell count rather than frame dimensions
  or density.

Implementation hypothesis: find 4-connected color-1 components whose bounding
box is a complete rectangular frame, extract every interior, and return the one
with the greatest count of cells other than 0 or 1. Remaining uncertainty is tie
behavior, which is not exercised by the visible examples.
