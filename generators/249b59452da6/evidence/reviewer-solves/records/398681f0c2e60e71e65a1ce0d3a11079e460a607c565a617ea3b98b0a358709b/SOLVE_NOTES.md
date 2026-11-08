# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Earlier exposure: none known. I did not open this task's generator, rule, private
labels, prior solutions, or audit records.

Hypothesis from the three visible examples: scan each 2x2 window in the original
input. When red cells (2) occupy exactly one diagonal and the other two corners
are both background (0), recolor those two background corners green (3). This
turns an isolated diagonal red pair into a red/green checkerboard. Use the
original grid for all detections so newly added green cells cannot create or
block later detections. Preserve every nonzero distractor/marker; a marker or a
third red cell in either cross-corner blocks that 2x2 completion.

Evidence checked manually:
- Example 0's lower zigzags consist of qualifying diagonal red pairs, while the
  upper-right pairs are blocked by an existing red or a color-5 marker.
- Example 1's isolated diagonal pair, two three-step diagonals, and two branches
  receive exactly the shown cross-corners; the color-9-marked cluster is blocked.
- Example 2's left and lower-right diagonals qualify, while the color-5-marked
  component does not.

Alternative considered: decorate whole connected components or copy a stencil
suggested by the two marker pixels. That is unnecessarily global and predicts
extra green cells; the local 2x2 condition explains every changed and unchanged
cell in all visible examples.

Remaining uncertainty: private queries could distinguish whether overlapping
qualifying windows are evaluated simultaneously. The examples support reading
from the original input, which the implementation does.
