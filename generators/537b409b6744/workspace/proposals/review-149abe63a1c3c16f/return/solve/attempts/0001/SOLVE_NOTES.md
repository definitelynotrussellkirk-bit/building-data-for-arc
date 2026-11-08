# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — nearest mover passes through the larger wall

Earlier exposure: **yes**. I reviewed this task's generator and rule before this
required post-repair visible-only solve. During the solve itself I consulted only
the prepared visible examples, the local solution file, and visible checker
feedback; I did not reopen the generator, Racket rule, reference solution, or
private query labels.

Visible hypothesis: the modal color is background. Non-background same-color
components form objects. A small object qualifies against a solid rectangular
wall when they face one another, overlap on the transverse axis, and the wall is
strictly wider/taller. The candidate with the smallest gap moves. Its original
cells are erased; a mover-wide channel is cut through the wall; the wall grows
outward on both transverse sides by at least one cell; and the mover reappears
flush on the far side. If the wall touches the grid edge, the mover occupies the
far end of the cut channel inside the wall. A farther qualifying object remains
unchanged and distinguishes nearest-object selection.

Checks from the three demonstrations:

- Example 0 selects the two-cell vertical object above the bottom wall, cuts its
  one-column channel, widens the wall left/right, and tucks the mover into the
  bottom of the channel because the wall meets the lower edge.
- Example 1 selects the two-cell horizontal object below the top wall, cuts two
  columns, grows the wall left/right, and tucks the mover into the top edge.
- Example 2 is the horizontal transpose: cut a one-row channel through the
  right-edge wall, grow it above/below, and tuck the mover into the right edge.

The implementation independently extracts connected components and reproduces
that geometry. Before implementation, a visible-only test over all three
training pairs failed with the template's `NotImplementedError`.
