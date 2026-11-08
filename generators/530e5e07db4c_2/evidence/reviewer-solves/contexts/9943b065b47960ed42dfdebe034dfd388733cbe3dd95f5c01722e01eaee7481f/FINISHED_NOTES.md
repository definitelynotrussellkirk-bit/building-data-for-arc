# Solve notes

This is a human work log based only on the visible challenge prepared from the final generator bytes. I had earlier rule exposure from reviewing the generator, so this is intentionally recorded as exposed rather than blind; I did not consult the generator, Racket source, reference solution, or private query labels during this solve phase.

## Revision 1 — connected red/green component

Across all three visible examples, color 5 is split into a large component containing both the unique red 2 and green 3, plus one disconnected two-cell decoy. Exactly the 5-cells in the red/green component become 4. The examples also rule out “all gray,” because the decoy remains 5, and rule out “one path only,” because branches and a large blob are recolored.

Probe/implementation: breadth-first search from the unique red cell over colors `{2,3,5}` using four-neighbor adjacency. If the reached set contains the unique green cell, change every reached 5 to 4; otherwise return the input unchanged.

For query 0, the red cell touches the large rectangular-ring component through the gray cell immediately to its left; the separate pair at the upper right remains 5. For query 1, the red and green cells are endpoints of the large central gray component; the separate vertical pair at the right remains 5.
