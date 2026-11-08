# Post-repair solve notes

This is a human work log, not a token-level model trace. I had already inspected the
selected rule while repairing the generator, so this episode is **not blind**. During
this solve phase I used only the visible examples printed by `solve_episode.py prepare`
and did not reopen the generator, Racket source, private labels, or earlier solution.

Hypothesis from the three demonstrations: retain the input and reflect every orange
(7) cell across the horizontal midline, preserving the column. For a grid of height
`h`, source `(r, c)` adds `(h - 1 - r, c)`. Example 2 is especially diagnostic because
all sources begin below the midline and their copies appear above it; therefore the
operation is not restricted to top-half sources. Examples 1 and 2 include repeated
rows/columns and adjacent cells, so every source participates independently.

I implemented that rule directly. No diagnostic or deliberately wrong revision was
needed before the first visible check.
