# Solve notes — 5a70e1b62a50

This is a human-readable work log based on the visible examples produced by
`solve_episode.py prepare`. I had already inspected this task's generator and
canonical rule during the repair phase, so this is **not blind**; I did not reopen
or consult those sources during this solve episode.

## Revision 1 hypothesis

The examples distinguish topological enclosure from global bounding-box filling:

- A zero component touching the canvas edge stays zero.
- A zero component that cannot reach the edge through 4-neighbor zero cells is
  filled with its sole adjacent nonzero color.
- Multiple disconnected closed holes are filled independently.
- In query 0, the upper rectangle is closed, while the lower U-shaped object is
  open to the outside and should remain unfilled.

I implemented a 4-neighbor flood fill over every zero component. For each
component I record whether it touches the border and the set of adjacent
nonzero colors; I paint it only when it is enclosed and that set has size one.
The implementation copies the input and does not mutate it.
