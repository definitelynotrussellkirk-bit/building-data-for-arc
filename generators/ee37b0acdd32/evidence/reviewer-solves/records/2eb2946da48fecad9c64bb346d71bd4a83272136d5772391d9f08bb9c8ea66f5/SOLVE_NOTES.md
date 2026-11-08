# Solve work log

I had not opened this task's generator, Racket rule, private labels, prior solve explanations, or the assigned repair generator before preparing this episode. I used only the visible examples printed by `review.py blind prepare`.

## Revision 1 — component-chain hypothesis

Across all three demonstrations, colors 1 and 2 are singleton endpoint markers. The other nonzero cells split into monochrome, 4-connected components. Components touch one another edge-to-edge, forming a mostly chain-shaped graph with dead-end branches. The output keeps exactly the components on the route from marker 1 to marker 2, recolors every retained cell 8, and clears every branch or unrelated component to 0.

Concrete observations:

- Example 0 follows `1 -> 9 block -> 3 connector -> 4 block -> 2`; color 7 and the lower color-3 singleton are side branches.
- Example 1 follows `1 -> 9 -> upper 4 -> 3 -> 5 -> 2`; color 6 and the lower color-4 singleton are branches.
- Example 2 follows `1 -> 4 -> 6 -> 2`; color 5 is a branch.

I implemented same-color connected-component extraction, an orthogonal-touch adjacency graph, breadth-first search from the color-1 component to the color-2 component, and output of the resulting path in color 8. BFS is a conservative choice if a generated graph contains more than one route; the visible lessons suggest a unique intended route, so shortest and unique coincide here.

Remaining uncertainty before checking: the hidden query might contain multiple marker components or a cycle. The visible data do not establish a tie-break for multiple equally short routes, but both displayed queries appear to have a single route with branches.
