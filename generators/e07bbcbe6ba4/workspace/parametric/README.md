# Distance and marker-origin family

`adapter.py` implements the native `program(settings)` and
`generate(seed, settings, demos, queries)` API. `promotion.json` declares four
settings. The default is byte-for-byte the selected canonical Racket program.

| Parameter | Values | Default |
|---|---|---|
| `distance_metric` | `chebyshev`, `manhattan` | `chebyshev` |
| `origin_mode` | `marker`, `nearest_wall_reflection` | `marker` |

`marker` preserves the original frame/marker fill. The reflection alternative
finds the marker's unique nearest frame wall, reflects the marker across the
frame midpoint in that wall's axis, clears the old marker, then runs the chosen
fill on the resulting grid. A top/bottom wall selects row reflection; a
left/right wall selects column reflection. Both parameters remain fixed across
every pair in an episode. Manhattan parity is algebraically equivalent to a
marker-phased checkerboard; it is not claimed to require full distance recovery.

## Generate and inspect

From the extracted packet's outer directory, after its documented setup:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/e07bbcbe6ba4/workspace/parametric/prototype.py \
  build-evidence --out ../checks/e07bbcbe6ba4/replay
```

Use a new output directory. This produces four examples with **three demos and
four queries each**, executes all labels through protected Racket, checks the
declared rivals using demos alone, exercises the count boundaries, replays the
canonical pairs, and retains the concrete before/after teaching counterexample.
The private examples contain `program_solution`, settings, all query answers,
geometry and teaching receipts. The adapter accepts independent demo counts
**2–6** and query counts **1–4**. Defaults for the prototype are three and four.

```python
episode = adapter.generate(
    seed=17,
    settings={"distance_metric": "chebyshev",
              "origin_mode": "nearest_wall_reflection"},
    demos=3,
    queries=4,
)
```

Load `adapter.py` by its exact file path, as the native consumer does. The
adapter itself loads its adjacent prototype by exact path under a unique name.
No sibling checkout, environment, model, or external data is needed.

## Teaching and input coverage

Input RNG streams depend on seed, role and pair index, never on settings.
Changing the query count preserves all demos and the first query. The first
two demos deliberately cover both nearest-wall axes and opposite marker parity
under both origins, with equal frame-center parity to reject the center-origin
shortcut. The second has a long frame that exposes distance caps.
Seeded draws vary frame geometry, margins, side and marker position; they do not
reuse one fixed lesson for every seed. Extra demos and four queries are distinct.

Four-query canvases are 9×9, 21×23, 25×27 and 30×30. The largest has a 24×24
frame and 22×22 interior: the fill covers substantial content rather than empty
padding. Frame sizes remain 7–24 and keep an exterior margin. Markers include
edge-adjacent and deep cases. The admitted grammar has exactly one full frame
and one interior marker, colors 0/3, and a **unique** nearest wall. Ties and
additional colored distractors are outside this grammar. The canonical rule
and canonical generator remain unchanged, including their wider marker domain.

Each generated lesson rejects 13 explicit wrong candidates with demonstrations
alone: the other three native settings, frame-center origin, four incorrect
reflection choices, fixed canonical bounding box, two fixed checkerboard phases,
and distance caps 4 and 8. A rival runtime error raises; it is never counted as
successful teaching. Finite rival elimination is not universal rule uniqueness.

## Controller and public projection

`public_challenge(episode, query_index=i)` reveals exactly the original demos
and query `i`, without its answer, future queries, settings, turn count, program
or private identity. The existing controller owns answer/history sequencing.
`write_public_queries` writes one independent public file per query. Filenames
are SHA-256 hashes of the exact visible bytes using `reviewer_support`; the
private map alone retains ordering and episode association. Duplicate public
payloads are rejected. Give a model one chosen file, never the entire public
directory. Requesting one query gives identical first-turn bytes to a four-query
request with the same seed, setting and demo count.

The pre-v2 files in `evidence/retained/` are inherited provenance. Their old
setting-named public paths are superseded and must not be used for model input.

## Native handoff

After source/evidence inventory refresh, run the packet's native qualification:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles \
  parametric qualify e07bbcbe6ba4 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/e07bbcbe6ba4/qualification
WORK/.venv/bin/python review.py run python3 \
  generators/e07bbcbe6ba4/workspace/parametric/prototype.py write-witness \
  --qualification ../checks/e07bbcbe6ba4/qualification/qualification.json \
  --out ../checks/e07bbcbe6ba4/sequential-dependency.json
```

Qualification independently re-executes the adapter labels and all four native
settings, fitting them to demonstrations only. The causal witness executes both
the composed program and a skip-reflection counterfactual, records the actual
intermediate grid, and requires differences in ordinary painted cells. Its
source binding is copied from the passing qualification.

The reviewer returns source, inventory, execution evidence and qualification.
The owner must qualify and accept the exact integrated bytes. This prototype
does not self-accept, edit production approvals, or admit training trajectories.
