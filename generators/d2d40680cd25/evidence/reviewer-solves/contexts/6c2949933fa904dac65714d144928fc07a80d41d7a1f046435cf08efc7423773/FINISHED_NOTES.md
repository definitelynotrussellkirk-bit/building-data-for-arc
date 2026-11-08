# Post-repair visible-only solve notes

This is a human work log, not a blind trace. I had already reviewed the task's
generator and rule family before this episode, so earlier exposure is **yes**.
After `solve_episode.py prepare`, I consulted only `solve/challenge.json` while
writing and checking this solution; I did not reopen the generator, Racket rule,
canonical data, reference solution, or private labels.

## Hypothesis 1

Each same-colour 4-connected nonzero object is rigid. Colour 8 is a fixed cyan
vertical wall. Every other object falls straight downward as far as possible,
without rotation or deformation, stopping at the floor, the wall, or another
settled object. Lower objects must be settled before upper ones so stacked
objects do not pass through one another.

Visible evidence:

- In all three demonstrations, L-shaped objects retain shape and colour while
  translating vertically.
- Objects in lanes away from cyan reach the bottom row.
- An object whose footprint overlaps the cyan column stops directly above the
  wall.
- The first query has two adjacent horizontal bars above the same wall edge;
  it distinguishes independent floor falling from bottom-up stacking.

## Probe and implementation

I implemented same-colour 4-connected component extraction, excluded colour 8
from movement, sorted movable components by their lowest row, and repeatedly
translated each body downward until the next step would leave the grid or hit a
nonzero cell outside that body. Repeating sweeps handles any dependency exposed
by earlier moves.

Expected query behavior before checking:

- Query 1: the lower colour-1 bar stops one row above the wall; the colour-9 bar
  rests one row above colour 1; the colour-3 L falls to the floor.
- Query 2: colour 7 stops above the wall and colour 6 stacks immediately above
  colour 7.

No alternative hypothesis or fabricated failed revision was needed.
