# Solve work log

## Initial exposure

I had not opened task `91ba301501c5`'s generator, Racket rule, canonical record,
reference solution, private labels, or earlier solve notes. I used only the visible
examples produced by `solve_episode.py blind prepare` and `challenge.json`.

## Hypothesis 1

Each grid contains a solid gray (`5`) divider. The sparse blue (`1`) and red (`2`)
markers become straight rays perpendicular to that divider:

- blue (`1`) extends **away** from the divider to the outer grid edge;
- red (`2`) extends **toward** the divider, stopping on the cell adjacent to it;
- the divider and original markers remain unchanged.

Evidence: in train 0, blue markers above the divider extend upward while blue
markers below it extend downward. Red markers do the opposite. The same directional
relationship holds for every marker in all three visible examples.

## Probe and implementation

I first added `test_solution_visible.py`, which runs `solve` against all visible
training pairs. It failed on the untouched stub with `NotImplementedError`, as
expected. I then implemented the inferred rule. The implementation detects a solid
gray divider row and also handles the symmetric vertical-divider case, although the
visible examples are horizontal. Rays fill background cells only so another explicit
marker is not erased if paths meet.

Remaining uncertainty: the queries may contain a collision pattern or divider
orientation absent from the demonstrations. The inferred color/direction relation is
otherwise consistent across every visible marker.
