# Solve work log

## Exposure

Before this solve I had not opened this task's generator, Racket rule, reference
solution, private query labels, notes, or audit records. I used only the visible
examples printed by `python3 review.py blind prepare` and `challenge.json`.

## Revision 1 — flood the marked chamber

**Observation.** Every input has gray (`5`) walls, black (`0`) open cells, and one
red (`2`) marker. In each output the red marker becomes azure (`8`), as do exactly
the black cells reachable from it by four-neighbor movement without crossing a
gray wall. Black cells in other wall-delimited chambers remain black. The third
training example is the strongest discriminator: only the small bottom-right
chamber is recolored, rather than all black cells or one side of the grid.

**Hypothesis.** Treat gray as an impassable wall and flood-fill the connected
component containing the unique red marker; recolor that component azure while
preserving all walls and disconnected black pockets.

**Probe.** Before implementation, importing the starter `solve()` and applying it
to training example 0 failed with `NotImplementedError`, confirming the check
would detect the missing behavior. After implementation I compared all three
visible training outputs exactly.

**Alternatives rejected.** Recoloring all non-gray cells fails on the isolated
black chambers. Filling a rectangle or a side selected by the marker fails on
irregular wall boundaries. Diagonal connectivity is unsupported by the examples
and would leak through corner contacts, so the implementation uses four-neighbor
connectivity.

**Remaining uncertainty.** The visible data always contains exactly one red
marker and uses gray as the only wall color. The solver validates the single-marker
assumption and otherwise follows the demonstrated color roles.
