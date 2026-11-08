# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Prior exposure declaration before revision 1

I already inspected this task's generator and authoritative rule while repairing it, so this is an **exposed** post-repair solve, not a blind solve. During this solve phase I did not reopen the generator, Racket source, reference solution, or private labels. I used only the visible examples printed by `solve_episode.py prepare`.

## Revision 1 hypothesis

Each color-1 connected component is the perimeter of a rectangle with exactly one non-corner perimeter cell missing. For every component independently:

1. Find its bounding box and missing perimeter cell.
2. Fill background cells strictly inside the box with color 2.
3. From the missing cell, extend color 2 outward in the side's normal direction through background cells to the grid edge.
4. Preserve all color-1 cells and any non-background cells encountered by a beam.

The three visible demonstrations distinguish the canonical 4x4 case from wider/taller rectangles: train 0 is 4x4; train 1 is 4x5 and opens left; train 2 is 5x4 and opens up. Multiple query objects should all be processed. A beam may cross another object's box, so components and gaps must be read from the original input while writes accumulate in a copied output.

I implemented a general component/bounding-box solver rather than hard-coding positions, sizes, backgrounds, or object counts.
