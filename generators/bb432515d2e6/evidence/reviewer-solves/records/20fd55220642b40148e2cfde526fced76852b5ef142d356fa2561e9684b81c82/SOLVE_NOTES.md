# Human solve work log

I used only `solve/challenge.json` during this solve phase. I had earlier rule exposure from the generator review, so this is an exposed post-repair solve rather than a blind solve.

## Hypothesis 1

Color 5 forms impassable walls. Every other nonzero color is a source. Each zero receives the color of the uniquely nearest source under four-neighbour shortest-path distance through non-wall cells. A zero remains zero if no source reaches it or if different source colors tie.

Evidence in the three visible examples:
- The first example has three sources in an open chamber and keeps a zero boundary between equal-distance colors, rejecting arbitrary tie-breaking.
- The second example has an internal wall and a lower opening, so shortest routes must follow the traversable geometry rather than raw Manhattan distance.
- The third example leaves an entire walled, seedless chamber zero, rejecting a fallback fill for unreachable cells.

Implementation: one multi-source BFS per distinct source color, followed by a unique-minimum comparison at each original zero. Existing walls and source cells are copied unchanged.
