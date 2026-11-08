# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — union of graph-geodesics

Observed that 5-cells act as walls, 2 and 3 are endpoints, and selected 0-cells
become 8. A simple flood-fill cannot explain the second training pair because
large reachable areas remain 0. A single arbitrary shortest path also cannot
explain it because both equally short detours around the central wall are filled.

Hypothesis: color every traversable zero that lies on at least one shortest
4-neighbour path from 2 to 3. Equivalently, for a cell `v`, color it when
`dist(2,v) + dist(v,3) == dist(2,3)`. This explains:

- the full open rectangle between opposite-corner endpoints as the union of all
  monotone shortest paths;
- the five-row band around the obstacle as the union of the upper and lower
  shortest detours and all equally early/late turns;
- the horizontal corridor while excluding its vertical dead-end branch.

Implemented two breadth-first distance maps. Walls and endpoints are preserved;
only qualifying 0-cells are changed to 8. Remaining uncertainty is limited to
unseen inputs with multiple/missing endpoints, for which the implementation
conservatively returns an unchanged copy.
