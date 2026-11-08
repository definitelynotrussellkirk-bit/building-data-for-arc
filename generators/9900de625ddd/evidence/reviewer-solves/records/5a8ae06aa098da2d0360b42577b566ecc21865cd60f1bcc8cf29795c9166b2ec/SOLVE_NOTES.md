# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — one-step same-color erosion

Observed that every output preserves exactly the interior of each monochromatic
shape after removing its one-cell boundary in all eight directions. A solid 3×3
becomes its center; 3×4 and 4×3 rectangles become 1×2 and 2×1 cores. The 4×4
shape missing one corner loses the diagonally exposed candidate as well, which
selects eight-neighbor rather than four-neighbor erosion. Mixed-color 3×3 blocks
produce no output because their nominal center sees the contaminating color.

Implementation: for each nonzero cell away from the grid edge, retain it only
when all nine cells in its centered 3×3 neighborhood equal its color; otherwise
write background 0. Grid edges cannot survive because the outside is background.
No reference source, generator, private labels, or prior explanation was used.
