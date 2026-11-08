# Working notes: e5477d32d98b

## Current decision

The canonical production generator and selected forward Racket authority remain
unchanged. The task-local parametric family adds an episode-fixed `direction`
parameter with byte-exact `forward` default and a `reverse` alternative. Inputs
are matched across settings; 2–6 demonstrations identify the finite declared
rule family, and every episode retains four distinct queries.

The sequential dependency is: normalize both source objects and compute the
selected directional difference; use those input-dependent stencil coordinates
to paint the query object at its bounding-box origin. A protected-Racket
wrong-direction witness changes the final output.

The strongest concrete shortcut left by the canonical demonstrations is
`copy_after`: ignore the before panel and copy the normalized after occupancy
into the query color. Protected Racket confirms that it fits both canonical
demonstrations, but seed 17's first generated forward demonstration disagrees.
The exact input and both outputs are retained in
`checks/e5477d32d98b/shortcut-review.json`; the proposed sampler emits the
counterexample rather than merely describing it.

The maximum lawful input is 30×29 because three equal-width panels plus two
separator columns cannot total 30 columns. Authoring preflight, public projection,
first-turn privacy, and causal replay passed under `checks/e5477d32d98b/`.
Owner source review, native qualification on integrated bytes, and fresh
acceptance remain required; no training admission is claimed.
