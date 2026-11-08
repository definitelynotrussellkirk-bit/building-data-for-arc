# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — selector color plus object extraction

Earlier exposure: I had not opened the task's generator, Racket rule, private labels,
reference solutions, or prior solution notes. I had only read the visible examples
printed by `solve_episode.py blind prepare`.

Hypothesis: the component touching the upper-left corner is a selector token. Its
color identifies another object elsewhere in the grid. The output is the tight
bounding-box crop of the largest 4-connected component of that selected color,
with all cells outside that component rendered as background 0.

Evidence from the visible examples:

- Example 0 selects color 7 at (0,0); the other 7-component crops exactly to the
  shown 5x4 output.
- Example 1 selects color 8; the other 8-component crops to the shown 3x3 output.
- Example 2 selects color 6; the other 6-component crops to the shown 3x5 output.
- Query 0 is especially useful because the selector is a three-cell 9 component,
  not a singleton. This rules out simply deleting one top-left cell before cropping.
- Query 1 has a five-cell color-3 distractor tied in size with the main color-7
  object, so selecting the globally largest object is insufficient; the corner
  color must disambiguate it.

Implementation: find all 4-connected components of the corner color, discard the
component containing (0,0), select the largest remainder, and reconstruct only
that component inside its tight bounding box. Remaining uncertainty is limited to
an unseen case with multiple non-selector components of the selected color; the
examples support choosing the largest component rather than combining them.
