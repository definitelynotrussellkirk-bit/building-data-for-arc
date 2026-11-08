# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

I had not seen this task's generator, canonical rule, reference solution, private
query labels, prior solve notes, or audit records. I used only the visible grids
prepared in this directory.

Hypothesis: treat each column independently. For every maximal contiguous
vertical run of one nonzero colour, erase its interior and retain its top and
bottom cells. A singleton remains once.

Visible evidence:
- Train 0 turns the length-3 colour-9 run into its two ends, while the length-2
  colour-3 run and singleton colour-4 cell remain.
- Train 1 decomposes exactly into runs: colour 4 at column 1, colour 3 at columns
  5 and 6, and colour 1 at columns 6, 7, and 8. Every output cell is an endpoint
  of one such run, and every run contributes both endpoints.
- Train 2 gives the strongest disambiguation: colour 3 has runs at columns 5
  and 7, colour 5 one run at column 6, and colour 6 runs at columns 7, 8, and 9.
  The displayed output is precisely the union of those vertical endpoints.

Alternatives rejected from the examples: endpoints of whole connected
components (fails the multiple-column components), generic shape corners (would
not explain all long straight-column endpoints cleanly), and thinning or
alternating pixels (does not match the exact endpoints in Train 2).

Predicted query behaviour follows the same rule. Remaining uncertainty is only
whether an unseen nonzero background or ragged grid is allowed; all visible
examples use rectangular grids with background 0.
