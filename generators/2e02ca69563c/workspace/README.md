# Routing review tools

`../generator.py` is the selected implementation. These are task-local tools,
not alternate production implementations.

## Independent oracle

`review_oracle.py` implements frame recognition, local groups, H→V paths, a
path-conflict detector, and a hand-constructed cross-frame color-reuse witness.
It does not import generator code. Training/reference labels remain the canonical
Racket rule. The complete-lesson probe cross-checks this helper against Racket.

## Complete-lesson probe

From the extracted packet root, choose a **new** output directory:

```sh
python3 run_with_racket.py python3 generators/2e02ca69563c/workspace/lesson_probe.py \
  --seed-start 1000 --seeds 100 --out ../checks/lesson-probe
```

This uses public `Catalog.apply`, in batches at most 64, and binds every result
to the selected generator SHA and rule hash. It checks all usable canonical
train/test pairs and iterates the module's actual `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` declarations.
It never counts an execution error as a rival refutation.

For each difficulty and seed, indices 0–5 supply every cyclic starting position
0, 1, 2 of a three-demo/one-query lesson. Windows overlap. The summary reports
both draw counts and unique-grid counts; a surviving rival that fails the query
is reported as unresolved query discrimination, not a successful demo refutation.
A nonempty rival declaration and actual canonical pairs are required.

The JSONL reference file contains `{ "start_index": ..., "receipt": ... }`
records. `start_index` indexes canonical pairs first, followed by the saved
`draw-plan.json`. Each nested receipt includes exact input and output hashes.
Use a new output path for each run; the probe does not overwrite earlier evidence.

## Tests

```sh
python3 run_with_racket.py python3 -m pytest generators/2e02ca69563c/tests -q
```

`test_review_contract.py` has 28 regression cases. The original selected generator
fails 20 of those 28 cases; v3.0.0 passes all. `test_lesson_probe.py` adds two tests
for query ambiguity and exception accounting. The full repository test discovery
does not include this directory; run it explicitly.

Portable replay uses the public `prepare_runtime` layout and copies these tools
and tests next to its mapped task generator; no source-relative parent-depth
assumptions are needed beyond the stable task-local directory structure.
