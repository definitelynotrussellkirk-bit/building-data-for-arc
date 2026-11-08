# Native stacking order: near-first or far-first

This family preserves the exact canonical `near_first` Racket program and adds
`far_first`, which reverses only the order in which rigid colored objects are
slid toward the red edge.  The setting is fixed for the episode.  Inputs are
matched across settings and all scenes contain at least two collision chains,
so the first two demonstrations identify the order rather than merely teaching
edge attraction.

A is the placement of the first object under the chosen depth order; its
input-dependent intermediate is the occupied-cell set containing the red edge
and that moved object.  B slides every later object maximally against that
updated occupancy.  Changing the order changes the intermediate and therefore
where later objects stop.  The protected witness uses the opposite qualified
order as a `wrong_order` counterfactual.

Requests support 2–6 demonstrations and 1–4 queries independently.  Full banks
are prefix-stable, deterministic, setting-independent on input, and contain ten
distinct grids.  Queries include a substantive 30×30 scene with two collision
chains, multiple rigid shapes, all quadrants, and the red boundary.  The finite
self-audit covers the two declared orders, independent sliding, no stacking,
count boundaries, exact canonical labels, and bounded seed diversity; it does
not prove universal induction or training benefit.
