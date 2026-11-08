# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none. I had not opened any generator, Racket rule, reference
solution, private label, audit record, or prior solve explanation before this
attempt.

Hypothesis: the solid middle row is a separator between two equal-size 4×W
panels. Treat zero as background in each panel. The output is the cellwise union
of the two nonzero masks, recolored uniformly as 3.

Visible-example probes:
- Train 0 row 1: `01011 OR 11000 = 11011`, matching the output mask.
- Train 1 row 2: `0110001 OR 0001000 = 0111001`, matching the output.
- Train 2 row 3: `11000111 OR 00100000 = 11100111`, matching the output.
- The same relation holds for every visible row; overlap and differing source
  colors do not change the result.

Implementation: split at the unique structural midpoint (two equal-height
panels around one separator row), OR corresponding cells by nonzeroness, and
emit 3/0. I added rectangular-grid and odd-height validation. Remaining
uncertainty is limited to whether unseen inputs ever depart from the visible
`2h+1` stacked-panel layout; the examples give no evidence for another layout.
