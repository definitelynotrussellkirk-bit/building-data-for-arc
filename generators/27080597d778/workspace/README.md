# Reproducible tools for task 27080597d778

Run the following from the extracted **review packet root**, beside
`run_with_racket.py`. Install the bundled offline Racket with
`python3 setup_racket.py` first. Output paths must be new: tools refuse to
silently overwrite existing evidence. The library's NumPy/Pillow runtime is used;
no model weights, GPU, network access, or extra service is needed.

## Generate and validate actual lessons

```sh
python3 run_with_racket.py python3 generators/27080597d778/workspace/lesson_gate.py build \
  --allow-unapproved --count 8 --queries 2 --seed 117 --difficulty hard \
  --out ../checks/my-research-lessons

python3 run_with_racket.py python3 generators/27080597d778/workspace/lesson_gate.py audit \
  --episodes ../checks/my-research-lessons/episodes.private.jsonl \
  --report ../checks/my-research-recheck.json
```

`build` uses the library's existing `Catalog.generate` API with the generator's
`EXAMPLES_NEEDED` (four), then independently shuffles the actual demos. All labels
are executed by the unchanged canonical Racket rule. The final gate checks all
train and test pairs, matching source/rule metadata, nonempty integer grids,
input grammar, duplicate input leakage, input mutation, task lesson hooks, and
independent survival of every named rival. Missing contracts, failed reference
execution and later-query failures are not treated as success.

Successful output contains:

- `challenges.jsonl`: only ARC train pairs and test inputs — no query labels,
  source program, task ID, seed or provenance metadata.
- `labels.private.jsonl` and `episodes.private.jsonl`: evaluator/training-side
  answers and full source records. Never expose these to a challenge solver.
- `validation.json` and `manifest.json`: actual query-level verdicts, source
  hashes and output-file hashes. Admission is explicitly research-only.

Failed builds retain the rejected private episodes and `rejections.json`, but
emit neither public challenges nor a success manifest. CLI exits are 0=pass,
1=rejected data, 2=operational/input error. A rejection is evidence, not permission
to discard failures silently until a desired result appears.

The `audit` input is the library's **private rich episode JSONL**, not bare ARC
challenge JSON. It validates metadata and semantic content, not that every
sample index can be replayed to the same input. Optional sample-index metadata
must be unique and length-consistent. Program/source hashes are provenance and
staleness checks, not signatures against an adversarial file author. Run in a
fresh process with stable sources, as the CLI does.

## Source-bound distribution census

```sh
python3 run_with_racket.py python3 generators/27080597d778/workspace/lesson_gate.py census \
  --seeds 32 --indices 16 --report ../checks/my-census-after.json

python3 run_with_racket.py python3 generators/27080597d778/workspace/lesson_gate.py census \
  --generator ../.review/baseline/repo/generators/27080597d778/generator.py \
  --seeds 32 --indices 16 --report ../checks/my-census-before.json
```

Both runs use the selected canonical Racket rule and the current named-rival
contract, reporting their hashes. Every pair is executed, not Python-labeled.
The census `passed` field means successful execution/mirror parity, **not** a
quality-admission decision: inspect branch counts, canonical checker errors and
rival correctness. The frozen baseline intentionally passes execution while
showing zero fallback samples. The panel census is specific to this task;
`audit` and `build` can target another compatible generator via global
`--task-id TASK --library PATH` arguments **before** the subcommand.

## Regression and broader verification

```sh
python3 run_with_racket.py python3 -m pytest -q generators/27080597d778/tests
python3 run_with_racket.py python3 -m pytest -q
python3 run_with_racket.py python3 -m arcpuzzles check 27080597d778 \
  --battery --phase after --timeout 4000 --out ../checks/my-after-battery
```

The task tests include canonical acceptance, all branch windows, exact one/two-
pixel counterfactual edits, strict pins/rejections, deterministic replay, all-
query gating, label/source corruption, missing contracts, mutation and private-
answer separation. Tests use an independent audit predicate; root review probes
also perform actual Racket parity and spatial/color metamorphisms. The second
pytest command is the repository-default test suite, not the task-local suite.

## Deliberate boundaries

This is a task-local prototype, not a shared-exporter patch. Native three-demo
exports can still be underdetermined. Use the final-lesson gate after every
operation that can change a lesson. Four demonstrations are sufficient against
these eight declared wrong solvers, not every conceivable program. Native
unshuffled four-demo exports retain schedule-position cues; the provided build
path removes the fixed demonstration-position relationship. No training gain
or approval promotion is implied.
