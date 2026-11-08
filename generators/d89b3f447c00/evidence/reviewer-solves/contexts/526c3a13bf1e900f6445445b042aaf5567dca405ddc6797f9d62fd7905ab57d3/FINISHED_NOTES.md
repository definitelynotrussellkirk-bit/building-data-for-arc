# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial visible-only analysis

Earlier exposure before this blind solve: none known for this task. I used only the
visible grids printed by `python3 review.py blind prepare` and `challenge.json`.

Hypothesis: treat each nonzero color independently. Its cells identify the minimum
and maximum occupied row and column. Those extrema define an axis-aligned bounding
rectangle; the transformation adds the missing rectangle corner in the same color.
Some colors include an interior distractor (for example color 4 in train example 1
and color 6 in train example 2), so the rule should use extrema rather than assuming
there are exactly three cells. Existing cells and all background cells outside the
missing corner remain unchanged.

Predicted query additions:
- Query 0: color 3 at (4,0), color 7 at (5,2).
- Query 1: color 4 at (1,0), color 8 at (6,0), color 1 at (4,10),
  color 7 at (11,2), and color 5 at (8,5).

Probe: a local visible-example regression script first failed on the untouched
`NotImplementedError`, then passed after implementing the bounding-corner rule.
Remaining uncertainty: a color could theoretically have more than one absent
bounding corner, but every visible color has exactly one absent corner; the code
fills every empty corner so it remains faithful to the geometric completion rule.
