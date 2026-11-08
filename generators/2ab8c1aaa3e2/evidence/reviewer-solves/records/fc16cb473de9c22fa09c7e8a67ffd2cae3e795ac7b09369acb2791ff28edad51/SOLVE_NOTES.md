# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none to this task's generator, rule, notes, solutions, or private labels.
I only read the visible challenge prepared by `solve_episode.py blind prepare`.

Hypothesis: inspect each column independently. For a nonzero color that appears
**exactly twice in that column**, paint the inclusive vertical interval between
those two occurrences with that color. Columns containing three or more copies
of a color are deliberately not completed. All segment endpoints are collected
from the untouched input before painting, so an overwritten distractor cannot
become a new endpoint.

Evidence from the visible examples:
- Example 0 has four exact-two column pairs, all completed vertically.
- Example 1 completes color 9 in column 2 and overwrites the unrelated color-8
  distractor at row 8; color 8 in column 0 occurs three times and is not joined.
- Example 2 leaves the three color-2 cells in column 0 unjoined, while completing
  the exact-two color-2 pair in column 4 and the exact-two color-6 pairs in
  columns 3, 5, and 6.

Remaining uncertainty: visible examples do not specify precedence if two
completed segments of different colors overlap in one column. The implementation
uses a deterministic discovery order; the observed instances have no such
conflicting completed segments.
