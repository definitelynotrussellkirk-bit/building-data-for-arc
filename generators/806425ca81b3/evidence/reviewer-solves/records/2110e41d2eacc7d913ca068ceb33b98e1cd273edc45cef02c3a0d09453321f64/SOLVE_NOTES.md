# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — horizontal same-color completion

Earlier exposure before this solve: none to this task's rule, generator, solutions,
or notes. I only read the packet instructions and the visible challenge produced by
`solve_episode.py blind prepare`.

Hypothesis: each row is processed independently. For every nonzero color that
appears at least twice in that row, fill the background cells from its leftmost to
rightmost occurrence with that color. Singletons stay unchanged. Distinct colors
on the same row form separate, non-overlapping spans in the visible examples.

Evidence:
- Train 0 fills color 8 across rows 6 and 8 and color 5 across row 7.
- Train 1 contains two colors on row 2; each is completed only within its own span.
- Train 2 leaves the singleton color 5 at row 2 column 1 unchanged while extending
  color 4 from columns 3 through 10.
- Train 3 extends each repeated color horizontally and changes no other rows.

Implementation copies the grid, groups original nonzero cells by color per row,
and fills only zero cells between the extreme columns. Preserving existing
nonzero cells makes the behavior conservative if an unexpected span contains a
marker of another color. Remaining uncertainty: the visible lessons do not show
crossing spans, but the generator appears to avoid that ambiguity.
