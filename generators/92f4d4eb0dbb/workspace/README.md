# Workspace tools for 92f4d4eb0dbb

The selected implementation is `../generator.py`; workspace files are explicit
review probes and are never selected as production generator code.

## `reference_probe.py`

Independent task utilities used by focused tests:

- load canonical pairs and the selected generator;
- compute the normalized canonical rule hash;
- produce an independent strict-midpoint output;
- implement declared rival rules, including `inclusive_midpoint`;
- recover observable generator axes;
- execute batches through the selected Racket authority when available.

## `lesson_probe.py`

Source-bound lesson census for the ambiguity that all canonical pairs admit.
It prepares the selected task's portable runtime, dynamically consumes declared
rivals/witnesses, assembles the actual three-demo/one-query lessons, labels them
through a persistent selected Racket bridge, and writes counts for:

- materialized and identifiable lessons;
- exact unique inputs/pairs;
- schedule-profile and axis coverage;
- witness hits and rival survival;
- Python-oracle/Racket mismatches;
- canonical-shortcut fit and first disagreements;
- source hashes, sampler policy, and domain limits.

Example from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/92f4d4eb0dbb/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/92f4d4eb0dbb_lesson_probe_100.json \
  --timeout 1800
```
