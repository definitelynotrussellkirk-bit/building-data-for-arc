# Any or every shortest path

This opt-in family keeps the canonical blue start, red goal, gray walls,
cardinal movement and cyan answer cells. The episode-fixed parameter is
`path_mode`: `any` marks the union of all shortest paths; `every` marks the
intersection. Markers and walls are preserved. `any.rkt` is the exact canonical
program, including whitespace. The selected production generator and reference
authority are unchanged.

## Why this is a dependent computation

First find obstacle-aware distances from both markers and the optimal distance
`D`. A cell belongs to the shortest-path graph exactly when its two distances
sum to `D`. Next count graph vertices at each distance from the start. Every
shortest path visits exactly one vertex at each distance. Therefore a vertex
lies on **every** shortest path exactly when it is the only shortest-path
vertex at its distance. Every vertex in that graph occurs in some shortest
path, so a layer with multiple vertices has no mandatory vertex.

The second step depends on the first step's input-specific graph. Counting all
reachable vertices, ignoring walls, or substituting Manhattan distance changes
the answer. This is graph reasoning, not a fixed color remap. The protected
causal witness in the return substitutes Manhattan distance for `D` in an
actually qualified alternate program and checks that the answer changes.

## Sampling and teaching

`generate(seed, settings, demos, queries)` accepts exact integer seeds in
`0..2**63-1`, 2–6 demonstrations and 1–4 queries independently. Use three demos
and four queries ordinarily. Boolean counts/seeds, unknown settings and short
batches are rejected. Sampling is deterministic and independent of `path_mode`.
Separate split/index streams preserve the first query when requesting one or
four queries, and additional demonstrations do not consume query randomness.

The first demo is a chain of open rooms with alternating door positions. Its
middle row forces backward travel; one of three rotations reverses at least
one marker coordinate. This directly exercises the retained monotonic-motion
and northwest-marker-order audits. The second demo has a gate and an asymmetric
obstacle, including reachable cells outside the shortest-path union. Additional
demos use cyclic mazes and multiple barriers.

Four query families cover a 13×17 room chain, 21×25 maze, **30×30 room chain**
and 27×30 barriers, up to rotation/transposition. Rooms, walls, paths and gates
occupy the large canvases; these are not small puzzles surrounded by padding.
Minimum room geometry is 8×8. 8×30 and 30×8 boundary geometries are also tested.
Grid inputs admitted by the solver are rectangular 5–30 per side, colors
0/1/2/5 only, exactly one marker of each kind and a connected marker pair.
These broad solver semantics do not claim the sampler covers every possible
maze. The new grammar belongs to the separate parametric family.

`audit.py` tests the other setting plus six explicit rivals: monotone motion
along the major marker axis, a northwest-marker guard, ignoring walls, painting
all reachable cells, painting one arbitrary shortest path, and vertices
essential to **all** paths including longer paths. True labels are executed
through protected Racket. The additional rivals are Python hypotheses; their
execution is not mislabeled as Racket. An independent shortest-path-count
oracle and a separate vertex-deletion test check the singleton-layer method.
Finite rivals and sampled seeds do not establish universal rule uniqueness.

## Commands

From the packet root, using the interpreter that passed `python-check`:

```bash
python3 review.py run python3 -m pytest -q generators/498af9326ab9/tests/test_parametric_shortest_paths.py
python3 review.py run python3 generators/498af9326ab9/workspace/parametric/audit.py --out generators/498af9326ab9/workspace/parametric/evidence/new-audit
python3 review.py run python3 -m arcpuzzles parametric qualify 498af9326ab9 --out ../checks/498af9326ab9/qualification --summary
```

Audit and qualification destinations must be new. `promotion.json` supplies the
native adapter contract. `evidence/manifest.json` is produced by the native
manifest helper after focused checks. Qualification checks every setting on
two seeds and requires demonstration-only identification before checking the
four queries. Integration and fresh native acceptance on the owner's live
source remain required. This return does not activate training or change mix
weights, source approval hashes or existing audit resolutions.

## Public/private projection

`audit.py` writes content-hashed challenge bytes with the existing
`reviewer_support` projection. `public/` contains the complete four-query
controller bundles. **Do not show those bundles to a sequential actor.**
`public_turn(episode, query_index)` and the hash-named `public_turns/` files
contain demonstrations and exactly one query input, with no total-count hint,
future inputs, query answers, seed, settings or program. This is a projection
helper, not a new controller or training loop. The controller keeps the
query-index mapping in `private/exports.json` and chooses when to reveal it.
The first-turn payload is identical to generating only one query.

`private/execution.json` retains actual protected labels and runtime identity;
other private files retain rival counterexamples, boundary labels and settings.
The audit tests that hidden metadata and query answers do not affect public
bytes or IDs. Public file order is determined by content hashes; setting/seed
order appears only in private evidence.
