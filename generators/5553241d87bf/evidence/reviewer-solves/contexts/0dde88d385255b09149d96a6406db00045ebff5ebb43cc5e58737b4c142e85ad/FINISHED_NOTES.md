# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — exemplar replaces damaged tiles

I inspected only the visible challenge. Each grid is divided by all-zero rows and
columns into equal tiles. One tile contains nonzero colors other than the dominant
fill color; this is a complete marked exemplar. Other tiles are either solid or
contain one zero "damage" cell. In every training output, each damaged tile is
replaced wholesale by the exemplar at the same local orientation, while solid
tiles and divider lines remain unchanged. This also explains zeros in arbitrary
local positions being removed rather than merely recolored.

Implementation: detect non-divider row/column spans, take the most frequent
nonzero color as the fill, locate the tile containing another nonzero color, and
copy that exact tile into every tile containing an internal zero. Remaining
uncertainty: the visible examples contain one exemplar and rectangular regular
tiling; the code intentionally relies on that demonstrated structure.
