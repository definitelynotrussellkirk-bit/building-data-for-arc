# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — crop the figure and use the isolated color as a rotation code

I had no earlier exposure to this task's generator, reference rule, private labels, or prior solution notes. Each input contains one isolated cell whose color is in 1..4, plus a compact figure made from colors 5..9. The output discards the isolated cell and outer background, crops the figure to its nonzero bounding box, then rotates that crop clockwise by `(marker_color - 1)` quarter-turns: color 1 leaves it unchanged, color 2 rotates 90° clockwise, color 3 rotates 180°, and color 4 rotates 270° clockwise (90° counterclockwise). This exactly explains all four training pairs, including the output dimension swaps for markers 2 and 4.

The program locates the 1..4 marker, excludes that coordinate from the figure bounding box, crops from the original grid, and applies the corresponding number of clockwise rotations. The marker's spatial position appears incidental; the color-to-rotation mapping alone accounts for every example.
