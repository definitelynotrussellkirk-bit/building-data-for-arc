# Solve work log

I had already inspected the selected generator and reference authority while doing the assigned repair, so this is an exposed post-repair solve. During this solve phase I used only the visible challenge presentation and Python implementation; I did not reopen the generator, Racket rule, reference solutions, or masked labels.

## Revision 1 — exact translated-shape match

Across the three visible examples, color 5 makes an L-shaped frame near the upper-left. The nonzero, non-5 cells above and left of the L corner form a template. Exactly one external connected object has the same normalized cell coordinates in the same orientation; that object alone changes to 5. Rotated/reflected objects remain unchanged.

Implementation plan: identify the fullest row and column of color 5 as the L arms, extract the template from their upper-left rectangle, normalize its coordinates, enumerate cardinally connected nonzero/non-5 components, and recolor every external component with exactly the same normalized coordinates. This also handles templates and candidates translated anywhere in the grid without relying on their colors.

Visible query prediction: query 0 should recolor the color-6 object; query 1 should recolor the color-4 object. Remaining uncertainty is limited to unseen malformed frames or multiple exact matches; the visible examples consistently define a single L frame and one exact candidate.
