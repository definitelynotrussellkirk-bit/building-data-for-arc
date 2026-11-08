# Public parent 332f06d7 — authoring plan

Infer a rigid black block moving along a blue corridor toward a red destination.
Compute cell-wise geodesic distances from red through walkable cells; compute the
separate configuration-space graph of anchors where the entire black rectangle
fits. From the starting anchor, choose the reachable anchor minimizing the sum
of its footprint's goal distances. This reproduces all five original labels in
an exploratory Python calculation; every optimum is unique in those originals.

Build `travel=terminal|halfway`: canonical terminal position versus the midpoint
(rounded toward the endpoint) along a deterministic shortest legal anchor route.
Default bytes must equal the new reference. The route is a real input-dependent
intermediate, not a fixed translation. Generated corridors must include successful
arrivals, narrow bottlenecks, turns and misleading Euclidean proximity, sizes 1..4,
2–6 demonstrations, four distinct queries and a substantive exact 30x30 stress.

Implementation: failing official/hand-derived tests; general Python and Racket
rules; native adapter and legal corridor sampler; bounded adversarial self-review;
protected preflight, source-bound counterfactual replay and sequential public
exports. Row-major ties and midpoint path conventions are authored extensions,
not uniquely established by the finite original canonical examples. Keep source
and all tools task-local. Owner registration/acceptance remain separate.

## Final implemented rule and grammar

The general Racket reference matches all four original demonstrations and the
provided test gold. It treats 0/1/2 as black block / blue walkable cells / red goal,
and all other colors as walls. First flood cell-wise distances from the red goal.
Separately enumerate legal top-left anchors for the whole rectangular footprint,
flood reachable configurations from the start, and minimize the sum of goal
cell-distances under each reachable footprint. All five official optima are unique.
Canonical output restores the old black footprint to blue and paints the chosen
terminal. The `halfway` setting uses the middle anchor of a shortest legal route,
rounded toward its endpoint. Backtracking ties use row-major predecessor order.

This path-distance objective and midpoint tie convention are authored extensions:
finite official examples cannot uniquely determine behavior on arbitrary branched
mazes. The sampled family uses three-to-five-lane winding corridors with controlled
alcoves, k=1..4 square footprints, successful arrivals, goal-adjacent dead-end
extensions, and connected but too-narrow bottlenecks. Wall colors vary among 3..9;
black/blue/red retain their explicit semantic roles. Geometry is rotated/reflected.
The 30x30 query has a 4x4 block, five lanes, a late bottleneck, >550 walkable cells,
and a legal route exceeding 70 steps. It is not sparse padding.

The first implementation had a real minimum-lesson ambiguity in halfway mode:
scoring only the closest footprint cell and rounding down could match the two
visible examples but disagree later. The retained old-source counterexample
contains protected labels. Version 1.0.1 uses a 3x3 successful first demonstration
with an odd route length and a goal before a blue dead-end extension; a 4x4 blocked
second demonstration teaches clearance. Partial goal overlap shifts the first
route by at least two steps and odd length makes floor/ceil rounding distinguishable.

## Verification and limits

29 focused tests pass. The source-bound audit covers 64 seeds, both settings,
every demo count 2..6: 640 nested lesson views and 5,120 pair exposures, with zero
query-changing survivors among 15 declared Python rivals. Protected authoring
preflight matches all five originals and both setting/seed jobs. Twenty further
max-demo labels pass. The causal witness replaces whole-footprint clearance with
a top-left-point check; its wrong configuration-space route changes 32 cells in
the retained 30x30 halfway query. Construction and a separate live replay pass
(24 extra protected executions total). Sixteen single-query public views pass
saved-file validation and hidden-field/future-query invariance checks.

Native adapters retain four private queries and support independent 2..6 demos /
1..4 query prefixes. Public presentation shuffles the full bank before choosing a
turn, hashes visible bytes only and never exposes settings, programs, answers,
future queries or total count. Directory listings remain controller-private.

Task-local audit.py rejects stale source bindings and wrong runtime identity;
its `--preflight`, `--out`, `--seeds` interface is reusable after fresh preflight.
Final review is an author self-review; no independent reviewer was available.
Bounded seed/rival tests do not prove universal identifiability or training benefit.
Owner registration, native qualification and exact-source acceptance are pending;
this authoring return does not modify shared authority or admit training data.

## Current repeated-parent reconciliation

Preserve exact terminal and halfway rigid-footprint programs and all current winding-lane/bottleneck constructors. Port incoming route tracing onto the current goal-distance decoder, marking swept blue cells 9 and retaining destination black. Incoming dead-end route semantics remain proposals; compatible inputs are relabeled by incumbent semantics. Current evidence resides in evidence/repeat-eleventh-union. Private native acceptance and root publication are separate.
