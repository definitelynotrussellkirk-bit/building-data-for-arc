# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Mosaic audit

From the extracted packet root:

```bash
python3 run_with_racket.py python3 generators/02280b74c8ab/workspace/probe_mosaic.py \
  --seed-count 20 --joint-controls --out ../checks/mosaic-probe.json
```

The output path must be new. The wrapper changes the working directory to
`repo`; the report records that actual directory and the Python argument vector.
The tool also imports its own generator correctly when launched from another
working directory, using `reviewer_support.find_root(__file__)`.

The report includes all canonical pairs, every cyclic start of the schedule
declared by `SCHEDULE_PROFILES` for each of `None`, `easy`, `medium`, and `hard`,
and all five held-out-query rotations of every four-demo lesson. For a period
of five, each seed/band uses nine consecutive draws, five windows and 25 query
rotations. It reads and validates the generator's live `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, and `SEMANTIC_RIVALS` mappings, scoring their union once
per name/input hash. Authoritative labels come
only from public `Catalog.apply` calls of at most 64 inputs. A rival fitting all
four demonstrations and disagreeing on the query is retained as an exact
counterexample; agreement on the query is recorded as `survived_all`.

Single-axis boundaries and shape/texture combinations run by default.
`--joint-controls` adds all 80 combinations of the documented size, shape and
decor boundaries in every band and every schedule start. Successful controls
must pass the validator and match `observe_overrides` on the generated pixels.
Rejected combinations require structured incompatibility evidence. Exact
inputs and Racket outputs live in the report's `inputs` map; sample and
counterexample records refer to those content hashes. Source hashes and every
sample's seed, index and overrides are retained alongside them.

Exit codes are 0 for a completed finite audit without failures, 1 for measured
failures, and 2 for a run error. The `status` field remains authoritative for
partial reports. These are overlapping task-local schedule windows, not
independent production-sampler lessons. Neither a passing finite rival check
nor a marginal witness frequency establishes universal identifiability.
