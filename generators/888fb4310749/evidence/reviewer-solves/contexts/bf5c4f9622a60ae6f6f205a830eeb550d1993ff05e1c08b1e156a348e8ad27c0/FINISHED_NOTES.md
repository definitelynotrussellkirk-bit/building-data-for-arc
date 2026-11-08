# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: I had opened only the packet's generic `ARC-DESIGN.md` before
preparation; I did not inspect this task's rule, generator, notes, labels, or
solutions.

Hypothesis from the three visible examples: the nonzero cells form one solid
rectangle.  Copies "tumble" away from it in every diagonal direction.  Each
step is edge-adjacent vertically and horizontally, swaps height with width, and
is clipped by the canvas.  Even-numbered copies use the original colour; odd
copies use colour `9 - original` (2↔7, 3↔6, predicting 1↔8).  A ray stops once
its next full rectangle no longer intersects the canvas.

Probe: added `test_visible.py`, first observed the expected `NotImplementedError`,
then implemented the four independent tumbling rays.  Remaining uncertainty is
whether unseen inputs can use colour 9 or a nonzero background; the visible task
supports colours 1–8 on background 0.
