# Replaying review-faa6dc1d8ae4a1d2

Run from the extracted packet root after applying the generated source patch.
The tools do not modify the runtime and do not read reviewer-solve private labels.
Racket labels remain the authority.

## Fast checks

```sh
python3 -m pytest -q repo/generators/28e5fbc279ab/tests
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check 28e5fbc279ab \
  --battery --timeout 4000 --phase after --out ../checks/replay-after
python3 run_with_racket.py python3 -m arcpuzzles check 28e5fbc279ab \
  --stage lint --phase after --out ../checks/replay-lint
```

Final review result: 58 task-local tests passed and all 12 battery stages were
green for generator SHA-256
`d68ecb728463d4ffc5348ac5fbb10003abbc665c342adcfdc2cf5515a9770226`.
The inherited `test_generator_28e5fbc279ab.py` remains byte-identical to the
assignment baseline; new regressions are separate test files.

Output directories must not already exist. `run_with_racket.py` changes its
child working directory to `repo`, so paths beginning `../checks/` are relative
to that directory.

## Prepare a source-bound runtime

Use a fresh destination outside the source tree:

```sh
rm -rf .review/replay-runtime
PYTHONPATH=repo/src python3 - <<'PY'
from pathlib import Path
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime
prepare_runtime(Catalog(Path('repo')), Path('.review/replay-runtime'),
                task_ids=['28e5fbc279ab'])
PY
```

The runtime manifest must bind
`puzzle_generators/per_puzzle/28e5fbc279ab/generator.py` to the final hash above.

## Geometry and authority census

```sh
python3 run_with_racket.py python3 \
  generators/28e5fbc279ab/workspace/review_probe.py \
  --runtime ../.review/replay-runtime --phase final --per-band 400 --seed 101 \
  --out ../checks/replay-final-census.json
```

The retained final run sampled 1,200 draws (indices 0–399 at seed 101 in each
band): 1,200 unique inputs, 402 inputs with multiple green components, 72 unique
normalized reference shapes, and zero self-check rejections, footprint defects,
marker overwrites, mirror disagreements, or Racket/canonical mismatches.
`green_component_count` is a sum over components; use
`multiple_green_components` for the witness-draw count.

## Complete-lesson rival census

```sh
python3 run_with_racket.py python3 \
  generators/28e5fbc279ab/workspace/lesson_probe.py \
  --runtime ../.review/replay-runtime --phase final \
  --seed-base 101 --seeds 40 --starts 0,1,2 \
  --out ../checks/replay-final-lessons.json
```

This assembles 120 lessons per band from every cyclic schedule start. Each lesson
uses three consecutive demonstrations and the next consecutive query. The run
references 480 draws per band but caches them into 240 generated/unique inputs
per band (720 unique across bands). It dynamically iterates the loaded
`LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS`; every declared rival was refuted
by the demos in all 360 lessons, no query-relevant rival survived, all canonical
pairs matched Racket/stored outputs, and the declared canonical shortcut fit all
3 canonical pairs.

## Interpreting the probes

The probes establish the sampled, declared domain only. They do not prove unique
identification among arbitrary programs or model learnability. A final probe
exits nonzero on structural/authority defects or surviving declared rivals, but
exit 0 is not training admission. Exact reports are retained at
`checks/final-census.json` and `checks/final-lessons.json`.
