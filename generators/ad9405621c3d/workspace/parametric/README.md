# Maze routing through an input-derived waypoint

This separate native family keeps the exact selected canonical program as
`route_mode=direct`. `route_mode=via_farthest` first finds the cell with greatest
wall-aware shortest-path distance from the first row-major endpoint, then paints
the union of shortest routes from that endpoint to the derived cell and from
there to the other endpoint. Farthest-cell ties use row-major order. Each route
uses U,D,L,R BFS order. Endpoints are traversable in the alternate rule.

The choice is fixed privately for the whole episode. It changes the rule, not
the palette or input distribution. The first search supplies a new endpoint to
the second search; replacing that derived endpoint can change the final route.
This is a proposed native extension pending owner acceptance of its exact bytes.

## Implementation and verification plan

1. Preserve `canonical.rkt` byte-for-byte; implement `prototype.py`, thin
   `adapter.py`, and `promotion.json` with independent 3–6 demo / 1–4 query limits.
2. Build matched inputs with small interior detours and cyclic route choices,
   then independently audit labels and demonstration-only rival fit. Repair
   observed teaching holes before freezing the source.
3. Run focused task tests, generate the native source manifest, qualify both
   settings through protected Racket, and replay a causal counterfactual.
4. Use the packet's existing public preview exporter to save four separate
   single-query views. Keep its order map, settings and answers private.

`rivals.py` and `audit.py` are independent executable review tools. Their finite
rival bank is a bounded learnability check, not a uniqueness proof.

## Domain and sampler

Only 0 corridors, at least three 5 wall cells, and two matching colored endpoints are used. Endpoint
colors are 2,3,4,6,7,8,9. All non-wall cells are connected. The new sampler spans
7×9 through 30×30; its lattice maze fills the canvas with corridors, branches,
cycles and four boundary mouths. The production sampler's 6–9 × 7–9 envelope is
unchanged. The Python mirror validates a broader rectangular 2–30 semantics
domain; that does not claim the sampler emits every such grid.

One RNG stream per scene, plus an independent query-order stream, gives stable
count prefixes and identical inputs across settings. The sampler does not use
global random state. Three core demonstrations are selected jointly for both
settings from at most 400 constructed inputs, refuting all 19 direct-rule and
32 waypoint-rule rivals. Selection never reads query inputs or answers. It fails
loudly if no three-example cover is found. Two examples were attempted first:
the initial 45-rival design probe found no two-example cover for two of eight inspected
seeds, while three succeeded. This motivated a minimum of three, not a claim
that no conceivable pair can teach the rule. Extra demos retain independent
input streams. Four query profiles are shuffled independently of settings;
they include 7×9, 17×21, 25×29 and 30×30. An independently selected query makes
the farthest cell the goal, so the alternative can legitimately equal the direct
route. No D4 output-equivariance is claimed:
row-major endpoint order and U,D,L,R ties are orientation-sensitive.

## Run from the packet's outer directory

```sh
WORK/.venv/bin/python review.py run python3 -m pytest generators/ad9405621c3d/tests -q
WORK/.venv/bin/python review.py run python3 generators/ad9405621c3d/workspace/parametric/audit.py --out ../checks/ad9405621c3d/semantic-audit-new.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest ad9405621c3d --evidence generators/ad9405621c3d/workspace/parametric/evidence/current --include generators/ad9405621c3d/tests/test_parametric_native.py --include generators/ad9405621c3d/tests/test_parametric_rivals.py --reported-checks 'Use the actual current bounded check summary'
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify ad9405621c3d --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/ad9405621c3d/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/ad9405621c3d/qualification/qualification.json --out ../checks/ad9405621c3d/preview
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/ad9405621c3d/preview
```

Choose a new qualification/output path after source changes; an existing source
manifest needs its native guarded replacement. Never reuse another checkout's
runtime or approval. `qualified` and `ready` do not mean accepted or admitted to
training. Present exactly one selected `public/<hash>.json` per turn; the preview
directory listing and `private/` content reveal future queries and belong only
to the controller. The bundled exporter verifies serialized bytes and source
bindings; it does not rerun Racket or implement a turn controller.

## Repairs and retained limits

The initial randomly selected demonstrations did not reliably teach route tie
order, endpoint direction, graph versus Manhattan distance, farthest ties,
non-leaf waypoints or the direction of the second leg. Protected before-witnesses
are retained in the returned checks. The new three-example construction rejects
those executable alternatives on demonstrations alone. Exact canonical code also
treats any color occurring twice as a potential endpoint color, including wall 5;
the former two-wall API case is now rejected by the common grammar.

The production generator is unchanged. Its prior interior-monotone teaching
audit remains a production finding; the separate native demonstrations refute
that rival without silently clearing the production audit. The finite maze
grammar and tested rival bank do not prove unrestricted uniqueness, arbitrary
seed success, human difficulty, learning benefit, or training eligibility.

The initial 200-candidate cap rejected seed 27 in the independent 0–31 probe.
A retained failing regression motivated extending the same deterministic candidate
sequence to 400, preserving every earlier successful lesson and its query stream.
The repaired seed is checked explicitly; other unseen seeds may still fail loudly.
