# Independent selection-rule probe

`review_probe.py` is a task-local, reusable review tool for this component-selection family. It does not produce training labels: labels are obtained from the unchanged canonical Racket authority. Its independently implemented component extractor and eight-rule rival bank do not call the generator's private selection helpers.

From the **packet root**, after `python setup_racket.py`:

```sh
python run_with_racket.py python generators/f9099d7c7e31/workspace/review_probe.py --repo . --out ../checks/probe-new --seeds 16 --samples 8 --matrix --metamorphic
python run_with_racket.py python generators/f9099d7c7e31/workspace/review_probe.py --repo . --out ../checks/task-tests-new --self-tests
```

The wrapper enters `repo/`; the paths above intentionally reflect that. Choose new output directories for every run: existing paths are rejected to preserve failed evidence. Python 3.12+, NumPy, Pillow, pytest, Bash, Git, and Racket are supplied or described by the original packet. No network access or model weights are needed for these checks.

For a baseline comparison in the original assigned packet, add:

```sh
--source ../.review/baseline/repo/generators/f9099d7c7e31/generator.py
```

The tool copies a complete runtime before importing the Racket bridge. `--self-tests` additionally copies every task-local test and workspace Python module, because the packet's static runtime mapping otherwise omits newly added tests. This mode reports the actual test-source and generator hashes.

## Output contract

`report.json` contains generator/tool/rule/ledger/pair hashes, actual Racket identity, errors, eight-rival disagreement counts, all four sliding lesson-phase checks, canonical-support share, and coverage limits. `pairs.jsonl` retains full input grids, executed outputs, controls, and per-case errors. `counterexamples.html` is an offline numeric-grid gallery, not a screenshot-only report. `runtime_manifest.json` records the staged runtime. Exceptions leave `failure.json` and `traceback.log`; nonzero exit status means failure.

`--matrix` enumerates 576 axis combinations × three difficulty bands at seed 9917/index 2. The default 16-seed/8-sample invocation adds 384 defaults, five canonical pairs, and (with `--metamorphic`) 36 transformed cases. Both target-selection agreement and saved canonical labels are checked against real Racket execution. At least eight samples are required to cover starts 0, 1, 2, and 3 of a complete four-demo window followed by a query.

## Adapting this tool

Keep the independent observable extraction and counterexample receipts. For another family, explicitly replace the task identifier, authority selection, component model, finite rival bank, override domains, and symmetry assumptions; do not pretend this task-specific CLI is a universal ARC gate. Confirm a proposed rival is genuinely wrong on a lawful reference-checked witness before requiring its rejection. Generator `strict_canonical_like` is a retained profile metric, not an independent distribution-distance estimate.

The selected implementation remains `../generator.py`. This workspace is not automatically selected as a generator.
