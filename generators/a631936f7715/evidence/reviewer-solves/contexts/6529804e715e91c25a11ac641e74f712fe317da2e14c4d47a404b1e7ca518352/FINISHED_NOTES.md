# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial exposure and hypothesis

I had not opened any generator, canonical rule, reference solution, private
labels, audit evidence, or task-specific notes before this solve.  I used only
the visible examples printed by `review.py blind prepare`.

The repeated structure is a background of color 7, one or more 4-connected
objects made of color 6, and sparse marker cells in other colors.  In every
training example, a marker orthogonally touching a gray object disappears and
its color replaces every 6 in that object's 4-connected component.  Gray
objects with no touching marker remain gray.  An isolated marker also
disappears.  Examples supporting this:

- Train 0: the marker 1 at (2,0) touches the three-cell vertical gray object at
  column 1; exactly those three cells become 1.  The other gray components stay
  6.
- Train 1: the lower-left three-cell object touching marker 5 and the right
  four-cell object touching marker 8 are recolored, while the unmarked
  three-cell object remains 6 and the isolated 5 is erased.
- Train 2: all three gray objects are independently recolored by their touching
  markers (4, 2, and 3), with component sizes 3, 3, and 4.

I chose orthogonal rather than diagonal connectivity because the apparent
near-touching branches in train 0 must remain distinct for the shown output.
The implementation erases every non-6/non-7 marker first, floods each
4-connected 6-component, and paints it only when exactly one distinct marker
color touches it.  If a malformed or ambiguous object touches multiple marker
colors, it conservatively stays gray; no visible example exercises that case.
