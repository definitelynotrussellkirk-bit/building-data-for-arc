# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

- Earlier exposure before this solve: none. I had not opened any generator, rule,
  notes, solution, or audit evidence; I used only the prepared public examples.
- Observation: the top row (excluding the zero corner) acts as a column-color
  header and the left column acts as a row-color header. The only symbols in the
  body are 0, 1, and 2.
- Hypothesis: preserve the frame and zeros; replace each body `1` by the color at
  the start of its row, and replace each body `2` by the color at the top of its
  column.
- Cross-checks: in training example 1, row-key 7 turns both adjacent `1`s into 7;
  in training example 2, the body `2`s in columns headed 5, 7, and 4 become those
  three distinct colors. These cases distinguish row lookup from column lookup.
- Alternative rejected: treating 1 and 2 as a fixed palette substitution fails
  because their outputs vary by position. Swapping the two lookup directions
  fails on row-key 2 under column-key 5 in training example 0.
- Remaining uncertainty: none for rectangular examples using the displayed frame
  convention. The implementation preserves unexpected body values rather than
  inventing behavior not demonstrated by the examples.
