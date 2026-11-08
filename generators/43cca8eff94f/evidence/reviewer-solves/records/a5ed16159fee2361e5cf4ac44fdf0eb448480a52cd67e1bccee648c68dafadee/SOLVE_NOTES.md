# Solve work log

This is a human-authored work log. I had already inspected the selected task's
reference rule while repairing its generator, so this is **not blind** and I
will record earlier exposure as `yes`. During this solve episode I did not
reopen the rule, generator, reference solutions, private labels, or prior solve
explanations; I used only the visible challenge presentation.

## Revision 1

Hypothesis from the four visible examples: color 8 is stationary. Treat all
color-2 cells as one rigid object. Determine the unique cardinal direction that
moves the red object's bounding box toward the cyan frame's bounding box, then
translate the full red cell set repeatedly until one more step would collide
with cyan (or leave the grid). Preserve shape and all non-red cells.

Evidence in the examples:

- Example 0 translates right without deformation.
- Example 1 translates left.
- Example 2 translates down.
- Example 3 translates up.

Thus all four cardinal branches are directly visible. The implementation uses
actual occupied cells for collision rather than only bounding boxes, so an
irregular red shape remains rigid and stops at first contact. I expect query 0
to exercise the upward branch and query 1 the rightward branch.

Remaining uncertainty: none material within the visible domain. The examples
show one red object and one cyan frame; the code conservatively returns a copy
if either color is absent.
