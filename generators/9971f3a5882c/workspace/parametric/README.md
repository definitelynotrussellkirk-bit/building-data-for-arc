# Native nearest/farthest marker-selection family

This task-local family is **qualified but not owner-accepted**.  It exposes one
episode-fixed parameter, `marker_selection`, with values `nearest` and
`farthest`.  `nearest` is the exact canonical default; the selected production
generator and canonical ledger are unchanged.  Owner acceptance and training
admission remain pending.

Both settings first compute an input-dependent intermediate: the original sparse
color-3 lattice bounding box, full rows/columns, and color-6 markers partitioned
by the side on which they lie.  The second step consumes that partition to choose
the nearest or farthest marker on each occupied side, derive new boundaries,
move only source boundary lines, extend internal full lines, and restore all
markers.  The second step cannot be chosen before the first has classified the
markers.

## Native contract

- `adapter.py` exports `program(settings)` and
  `generate(seed, settings, demos, queries)`.
- `promotion.json` declares 2–6 demonstrations and 1–4 queries.
- `nearest.rkt` is the canonical program byte-for-byte.
- `native.py` constructs setting-independent inputs, deterministic prefix-stable
  demo/query streams, four distinct queries, and substantive 30×30 stress.
- Public challenge bytes contain demonstration inputs/outputs and query inputs
  only.  Settings, programs, seeds, future turns, and query labels stay private.
- `audit.py` replays labels and a finite shortcut inventory through protected
  Racket and writes source-bound evidence.

Run the reusable audit from the packet root:

```bash
python3 review.py run python3 \
  generators/9971f3a5882c/workspace/parametric/audit.py \
  --out generators/9971f3a5882c/workspace/parametric/evidence/current \
  --seeds 0 17 --demos 2 3 6 --queries 4
```

Run native qualification:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 9971f3a5882c \
  --out ../checks/9971f3a5882c/qualification --summary
```

## Current bounded evidence

The protected-Racket self-audit covers both settings, seeds 0 and 17, demo counts
2, 3, and 6, and four queries per job: 12 jobs, 53 distinct Racket executions
after caching, 12 30×30 queries, and no survivor among the alternate setting or
six declared shortcuts (`ignore_top_*`, unit expansion, boundary-only variants,
and identity).  The native qualifier independently passed four setting/seed jobs
with 32 protected-Racket executions.

The sequential-dependency witness corrupts the intermediate right bbox boundary
before side classification.  That reclassifies an edge-aligned top marker as a
right marker and changes 90 final cells.  The witness is bound to an exact
qualified query and replayed through protected Racket.

This evidence is finite.  It does not prove universal identifiability, owner
acceptance, production API integration, measured training gain, or training
admission.  `training_admitted` remains false.
