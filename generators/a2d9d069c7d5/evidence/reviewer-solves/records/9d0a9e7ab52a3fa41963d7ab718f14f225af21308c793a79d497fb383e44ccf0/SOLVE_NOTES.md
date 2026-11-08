# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — odd-rectangle center stamping

Earlier exposure before this solve: none to this task's rule, generator, private labels,
or prior solutions. I only read the packet-level instructions and the visible examples.

Hypothesis: color 7 is the background. The five-cell plus is a legend showing the marker
color. Every other foreground component is a solid rectangle. The output recolors exactly
the center cell of rectangles whose height and width are both odd, including 1×1, 3×3,
and 5×5 rectangles; even-sided rectangles are left unchanged.

Evidence from the examples:
- Train 0 changes two 1×1 objects, two 3×3 centers, and one 5×5 center to 9,
  while 2×2 objects remain color 1.
- Train 1 changes a 1×1 object and both 3×3 centers to 1, while 4×4 and 2×2
  rectangles remain color 8.
- Train 2 changes three 3×3 centers, one 5×5 center, and a 1×1 object to 3,
  while the 4×4 rectangle remains color 1.

Implementation: detect the most frequent background, identify the non-background color
forming an exact five-cell plus, find 4-connected components of every other foreground
color, verify each component fills its bounding box, and stamp the plus color at the
bounding-box center only when both dimensions are odd. Remaining uncertainty is whether
future instances can contain a non-rectangular target component or more than one target
color; the implementation conservatively ignores non-rectangles and supports multiple
target colors.
