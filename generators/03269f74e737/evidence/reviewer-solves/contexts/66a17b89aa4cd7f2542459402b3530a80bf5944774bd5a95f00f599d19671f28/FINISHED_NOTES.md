# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — translated one-cell template completion

Observed a full-height color-9 divider. The left panel contains a connected
foreground shape; the right panel contains translated copies missing exactly one
cell plus distractors. In the third training pair, a smaller disconnected domino
on the left would create false completions, so I treated the largest 4-connected
left component as the intended template.

Probe: wrote `test_visible.py` to replay all four public training pairs. It first
failed against the supplied `NotImplementedError`, then the first implementation
hit a tuple tie-break bug in component selection. After fixing that mechanical
bug, all four public pairs matched exactly.

Algorithm: remove the divider and left panel; scan every translation of the
largest component's bounding box in the right panel. Fill a location only when
all but one template cells already have the template color, the missing support
cell is background, and there are no same-colored extras inside the bounding
box. Other colors are preserved and cannot substitute for a missing support
cell. No rotations or reflections were needed by the visible examples.

Remaining uncertainty: unseen cases could use a tie between equally large left
components or permit transformed orientations. The visible evidence supports a
single translated largest-component template only.
