# Post-repair solve work log

Prior exposure declaration: I reviewed this task's generator and selected rule before this episode, so this is **not blind**. During the solve episode I used only the visible examples printed by `solve prepare`; I did not reopen the generator, Racket source, canonical labels, or private query answers.

## Visible-example hypothesis

- Color `1` is a fixed wall/frame and every other nonzero color is a singleton source/seed.
- Each original `0` is filled by the seed with the smallest four-neighbor path distance when paths may use every non-wall cell.
- If two or more seeds attain the same finite minimum, the cell stays `0`.
- Original walls and seed cells are unchanged.

Evidence from the visible demonstrations:

1. The open 6x9 example leaves an entire center column at `0`, exactly the equal-distance bisector between the two bottom-row seeds.
2. In the horizontal one-gap example, the lower seed reaches the upper region only through the opening; straight Manhattan distance would put some boundaries elsewhere.
3. The vertical one-gap example similarly requires routing around/through the wall opening, and all three seed colors expand.

## Implementation

Compute one BFS distance map per seed through cells whose value is not `1`. For each original zero, gather reachable distances, choose the unique minimum color, and preserve zero on a tie or if no seed reaches it. The implementation deep-copies the input and does not mutate the caller's grid.
