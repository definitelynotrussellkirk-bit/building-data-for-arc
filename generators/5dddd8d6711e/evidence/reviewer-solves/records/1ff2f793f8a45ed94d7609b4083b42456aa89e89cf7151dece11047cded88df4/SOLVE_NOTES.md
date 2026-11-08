# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — room-graph route with clue and geometric tie-breaks

I treated rows/columns consisting only of blue (1) and orange (7) as wall lines,
so the rectangles between consecutive wall lines are rooms and each orange wall
cell is a doorway between two rooms. Red (2) and green (3) identify the endpoint
rooms. The output paints every non-wall cell in the selected room route azure (8),
keeps all blue/orange wall cells, and clears unselected room contents to black.

Visible evidence:

- Example 2 has a unique one-edge route and paints exactly its two rooms.
- Examples 0 and 1 each have two equal-length room routes. The painted route is
  the one containing more nonstandard clue cells (gray 5); example 1 also rules
  out a longer route with the same clue count.
- For remaining ties, I use the shortest actual cell walk through the candidate
  rooms and their doors. This is needed for the two queries, where the room-level
  route can still tie. A final lexicographic route order is only a deterministic
  fallback and is not established by the visible examples.

A temporary visible-example regression test was run before implementation and
failed at the original `NotImplementedError`, confirming the test exercised the
missing solver. Remaining uncertainty: the exact intended last tie-break is not
explicitly demonstrated, and clue priority versus route length is only observed
for equal shortest routes.
