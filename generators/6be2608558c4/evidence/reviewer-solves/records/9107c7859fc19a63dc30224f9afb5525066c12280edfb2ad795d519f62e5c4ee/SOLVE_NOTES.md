# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: yes. Before this solve phase I reviewed the assigned generator and the canonical task while repairing it. During this solve phase I did not consult the generator, Racket authority, reference solutions, or private labels.

Visible-example hypothesis: the nonzero cells in the top-left 5x5 window form a monochromatic exemplar shape. Erase that window conceptually, split the remaining nonzero cells into 4-connected components, normalize each component to its bounding-box origin, and select the unique component whose binary shape exactly equals the exemplar. Return that selected shape cropped to its bounding box with every foreground cell recolored 2. Color, absolute position, area alone, and bounding-box dimensions alone are irrelevant.

Probe: implement the rule directly and submit it to the visible-only checker. Remaining uncertainty before checking: whether connectivity ignores color. Every visible body component is monochromatic and spatially separated, so this does not affect the displayed examples.
