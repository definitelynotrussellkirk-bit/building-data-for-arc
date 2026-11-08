# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — connect aligned yellow markers

Earlier exposure: none to task `306adf8e4c54`; I did not open its generator,
rule, notes, solutions, audit records, or private labels.

Observation: every changed output cell is color 4 and lies strictly between two
input 4s in the same row or column. Examples include the horizontal gap in train
1 row 2, the vertical gap in train 1 column 1, several independent spans in
train 2, and the vertical bridge in train 3 column 2. Colors 1 and 2 in train 3
are preserved and are not endpoints.

Hypothesis: for each row and column containing at least two original yellow (4)
markers, paint zero cells from the first marker through the last marker yellow.
Compute spans from the original input, not from newly painted cells, to avoid
unjustified propagation. Preserve nonzero distractors if one falls inside a
span; the visible data does not establish that they should be overwritten.

Predicted queries:
- Test 1 adds `(2,6)` and `(4,3)` in zero-based coordinates.
- Test 2 fills row 2 columns 3 and 5; column 5 rows 3, 5, and 6; and column 6
  rows 3 and 5. Existing cells remain unchanged.

Remaining uncertainty: visible examples contain no non-yellow cell inside a
required span and do not distinguish a single pass from transitive closure in a
specially arranged crossing case. The conservative original-endpoint rule is
best supported by the examples.
