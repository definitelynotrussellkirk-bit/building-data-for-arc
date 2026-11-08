# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

### Observations

- In every training example there is exactly one fully occupied 2×2 block.
- Reading that block in row-major order gives the four colors placed at the
  output's top-left, top-right, bottom-left, and bottom-right corners.
- All other non-background cells are distractors/position markers and disappear.
  Example 1's repeated color 2 at the input corners and example 2's four color-4
  cells show that frequency alone does not identify the payload.
- The output keeps the input dimensions and uses the modal input color as the
  background.

### Hypothesis and implementation

Find the unique 2×2 window whose four cells are non-background, then place its
four entries at the corresponding corners of a blank grid of the same shape.
The code deliberately requires uniqueness rather than silently choosing a block.

### Alternatives considered

A connected-component crop is less precise because the marker cells can touch the
payload (training example 2). Selecting four rare colors also fails in training
example 1 because payload color 2 is repeated among distractors. The solid-window
criterion explains all three examples directly.

### Predicted queries

- Query 0: corners are 8, 7, 1, 3.
- Query 1: corners are 3, 2, 8, 9.

Remaining uncertainty: the visible data does not show a nonzero background or
multiple solid 2×2 windows; the implementation handles a modal nonzero background
but rejects ambiguity.
