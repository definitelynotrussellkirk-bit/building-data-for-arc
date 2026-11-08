# Current authoring status — 16de56c4

Unapproved public-evaluation family. All three supplied training examples and
both supplied test answers match the general edge-seeded periodic-ray rule.
First infer the unique source edge and each same-color seed pair's spacing.
A later different-color control is hit only if its offset is divisible by that
spacing. A hit changes the entire run's color, including both seeds, and the
canonical rule stops at the control. Off-lattice controls remain unchanged and
are passed. Markerless runs reach the opposite edge's last lattice position.
Alternative: keep the same phase test and hit color, but continue after a hit.

The exact admitted grammar has one common source edge, two initial same-color
seeds per active line, and at most one later different-color control per line.
Ambiguous source edges and malformed grids are rejected by the Python boundary.
Original labels, integer-grid validation, four directions, off-lattice decoys,
backward recoloring, stopping and continuation are retained in private tests.
The base generator is self-contained; engine.py is a byte-identical snapshot
for native resource isolation, enforced by a test. Default Racket equals the
root reference bytes. There is no example lookup or gold in public exports.

Two distinguishing demos each include a true hit, an off-lattice control, a
longer-period hit and a markerless ray. Their source edges are orthogonal.
Inputs are shared across settings; 2..6 demos and 1..4 queries are independent
and prefix-stable. The four-query bank covers all four source edges. A 30x30
stress case has 12..16 active lines and dense unit-period boundary rays.
Public presentation shuffles the complete bank, then reveals one masked view.

The finite audit covers 15 total rivals (phase, period, recoloring, extent,
orientation and identity), 32 seeds, both settings and all five demo counts:
320 episodes and no harmful survivors. This is not universal uniqueness or
measured training benefit. Protected-Racket preflight covers all supplied labels
and sampled generated lessons; separate source-bound evidence replays a wrong
phase-intersection intermediate and generator-only relocation. Owner native
qualification, acceptance and training admission remain pending.
