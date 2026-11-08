# Workspace: 5dc10de63325

The selected implementation is `../generator.py`, version 4.0.0. `check_curriculum.py` reads that source, records its SHA-256, loads canonical pairs through `reviewer_support`, and checks the live rival declarations against independent literal glyphs.

## Review-packet commands

Run the following from the packet root, where `run_with_racket.py` is located. The wrapper selects the packet's Racket and runs its payload from `repo/`; payload script paths therefore start with `generators/`, and `../checks/` refers to the packet's evidence directory. Use fresh output names for repeated public checks and generation.

Inspect the curriculum tool's supported options:

```sh
python3 run_with_racket.py python3 generators/5dc10de63325/workspace/check_curriculum.py --help
```

Reproduce the bounded raw cycle probe. `--seeds 20` means seeds 0–19; the retained final report used the medium band. Additional bands can be supplied together. This probe does not apply the production materializer, duplicate filter, or identity filter.

```sh
python3 run_with_racket.py python3 generators/5dc10de63325/workspace/check_curriculum.py \
  --seeds 20 --bands medium --out ../checks/curriculum-replay.json
```

Run the portable task tests, including the duplicate-filter regression:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 5dc10de63325 \
  --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-replay
```

Generate a Racket-verified lesson with the required demonstration count:

```sh
python3 run_with_racket.py python3 -m arcpuzzles generate 5dc10de63325 \
  --count 1 --seed 319 --difficulty medium --train 10 --test 1 \
  --allow-unapproved --out ../checks/ten-demo-lesson.jsonl
```

**Keep `--train 10` explicit.** `Catalog.generate` defaults to three demonstrations; its Python equivalent must pass `n_train=10, n_test=1`. `--allow-unapproved` permits this review draw and does not grant approval.

Run the independent public semantic check with rotated query positions:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check 5dc10de63325 \
  --stage semantic_gate --phase after --require-rotations-identifiable \
  --timeout 1800 --out ../checks/semantic-replay
```

Run the public census on materialized lessons, with 100 lessons per band and every query rotation:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 5dc10de63325 \
  --per-band 100 --train 10 --test 1 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census-replay.json
```

## Standalone library use

From a library checkout with its declared runtime and development dependencies installed, the curriculum script also runs directly:

```sh
python3 generators/5dc10de63325/workspace/check_curriculum.py \
  --seeds 20 --bands easy medium hard --out var/checks/5dc10de63325/curriculum.json
```

For the public commands, use the installed `arcpuzzles` executable, choose the checkout with `--library .`, and place outputs under `var/checks/`. Racket must be on `PATH` or selected by `RACKET_PATH`. The portable tests use `find_root(__file__)` to bind canonical data and generator source to their own library or copied runtime.

## Reading the evidence

The raw cycle report exhausts each measured seed's cycle starts and holds out every pair in an eleven-pair window. Its legacy `production_*` fields refer to the final-position holdout of these raw windows; `materializer_applied=false` and no filters are applied. It reports rival disagreements, context-only predictor accuracy, count/profile coverage, canonical calibration, and source identity. Labels come from four literal glyphs selected by observed cyan count.

The public accepted-lesson evidence is separate: `checks/lesson-census-final.json` records 300 materialized lessons, 3,300 pairs, and 3,062 unique inputs, with no declared-rival ambiguity in 300 production query positions or 3,300 rotations. `checks/code-review/dedup-after-window-sweep.json` independently mirrors duplicate and identity filtering across 33,786 accepted windows. The seed-319 replay in the same directory uses actual Racket outputs and checks all eleven rotations. Use the public semantic check or retained `checks/racket-counts/` evidence for further executed Racket comparisons.

A pass covers the listed seeds, bands, rivals, and sampling procedure. It does not establish coverage after arbitrary external filters, with an explicit fixed count, or with fewer demonstrations. The final source's protected/free remainder alternation and the seed-319 regression address the observed duplicate-removal failure. See [../notes.md](../notes.md) for that scope, the exact controls, and the retained lawful-minimal-shape warning from shared defect lint.

## Score context-only shortcuts on accepted lessons

`score_context_only.py` accepts a complete retained shared lesson-census report as JSON or `.json.gz` and validates its retained data with the shared census validator. From the packet root, score the final compressed census with:

```sh
python3 repo/generators/5dc10de63325/workspace/score_context_only.py \
  --input checks/lesson-census-final.json.gz --out checks/context-accepted-replay.json
```

Use `checks/lesson-census-final.json` instead when the retained report is uncompressed. The scorer uses only the retained Racket labels. It evaluates the original query and every single-pair holdout of the accepted pairs, preserving the remaining demonstrations' order. It performs no Racket execution, input regeneration, or generator import.

The scoring scope is this task's four prescribed output glyphs. Reported context-only predictor accuracies apply to the accepted lessons in that input file; they do not establish universal identifiability or coverage under other sampling policies.
