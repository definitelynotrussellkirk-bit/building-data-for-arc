# Current decisions: ad9405621c3d

## Canonical production scope

Production version `3.0.0`, SHA-256
`390ee47af1dcb79f5aeb17c16a119cab7bc2e7c668be2ea9a5362b719e3a8126`,
and canonical `RULE_HASH=f19a9c2c6081` are unchanged in this return. The existing
sampler supports 6–9 by 7–9 mazes, three exact observable axes, four scheduled
profiles and cycle-safe branch growth. Its source-bound old checks remain
historical evidence, not reruns of the new native family.

The retained review-index finding remains applicable to production: an
interior-endpoint rival that only moves closer in Manhattan distance fits that
sampler's interior profiles. This return does not silently clear the production
audit. New native demonstrations explicitly refute it.

## Native parametric decision

`workspace/parametric/` adds a separate `route_mode` family:

- `direct`: exact selected canonical program, byte-for-byte.
- `via_farthest`: compute all wall-aware distances from the first row-major
  endpoint; select the greatest-distance cell, breaking ties row-major; then
  paint the union of U,D,L,R shortest paths start→waypoint and waypoint→goal.

The second search needs the input-derived waypoint. Manhattan-distance selection,
fixed/leaf-only selection, reversed second-leg routing and skipping the waypoint
are concrete wrong alternatives. A native source-bound causal replay records a
counterfactual with a different final grid. Both programs operate on the same
input grammar and use matched input streams; labels are independently executed
through protected Racket during qualification.

## Teaching repair and count cost

The initial two-example sampler had real ambiguities under route ties, endpoint
reversal, waypoint ranking/ties, leaf-only selection and second-leg semantics.
Protected before-witnesses and source snapshots are retained under
`checks/ad9405621c3d/final-review/` and in the semantic before audit.

The finished API supports 3–6 demonstrations (default 3), and independently 1–4
queries (default 4). Before increasing the minimum, a bounded design probe tried
joint two-example covers of the initial 45-rival bank: six of eight seeds found a pair;
two needed three within that candidate pool. This is a bounded search result,
not an impossibility theorem. The final sampler selects a three-example cover of
19 direct and 32 alternate rivals from at most 400 constructed connected-maze
inputs, using no query data. Failure to find a cover is explicit and bounded.
Every supported larger demo count keeps the same three-example core.

## Domain, stress and limits

Inputs contain only 0, 5 and exactly two same-color endpoints in
{2,3,4,6,7,8,9}, with all non-wall cells connected. Require at least three walls:
exact canonical selection also considers wall 5 if it occurs twice, so the old
broader Python grammar could mislabel a two-wall scene. The regression rejects
that case instead of changing the canonical program.

The separate lattice-maze sampler adds cycles, varied endpoints and border
mouths across the canvas. Four shuffled query profiles include 7×9, 17×21,
25×29 and substantive 30×30. One independently chosen query has the goal as the
farthest cell, so routing via it is an honest inactive case. No output rotation
invariance is claimed because endpoint and BFS tie orders are directional.

The reusable independent `rivals.py` and `audit.py` retain exact executable
countermodels, source hashes, sampler successes/failures and real Racket counts.
Native inventory, qualification/execution, causal replay and single-query public
projection are the authoritative handoff receipts. Finite checks do not prove
unique induction or universal seed success. Owner acceptance of the exact
integrated source remains pending; no training admission is granted.

The initial 200-candidate cap rejected seed 27 in the independent 0–31 probe.
A retained failing regression motivated extending the same deterministic candidate
sequence to 400, preserving every earlier successful lesson and its query stream.
The repaired seed is checked explicitly; other unseen seeds may still fail loudly.
