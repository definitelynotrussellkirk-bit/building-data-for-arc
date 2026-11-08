# Bounding-box outline thickness — proposed prototype

This task supports one small semantic parameter: **inward outline thickness**, an
integer in `{1, 2}`. The original/default setting is **1**. It uses the exact
canonical `program_solution` string from this checkout's `puzzles.jsonl`, without
rewriting that source. Setting **2** replaces the boundary predicate with
`distance from the nearest bbox edge < 2`. Both programs replace every same-color
four-connected component with a band of its own color, on a zero background,
discarding the original interior shape.

This is a runnable, task-local **prototype**, separate from the selected
`generator.py` and its canonical repair. It does not modify or implement a
production parametric-rule API, change reference authority, or approve the new
rule. Its input sampler is independent of the selected production generator.

## Execute and reproduce

From the outer extracted packet, with its installed runtime dependencies:

```bash
python3 review.py run ../.venv/bin/python generators/623cca1dd5a8/workspace/parametric/prototype.py --out ../checks/parametric/run-001 --seeds 8
python3 review.py run ../.venv/bin/python -m pytest generators/623cca1dd5a8/tests/test_parametric.py -q
```

The evidence directory must be new. The wrapper selects the included Racket and
runs the payload from `WORK/repo`. `--seeds 8` means seeds 0 through 7, both
settings at each seed. In an installed repository, use the same payload with
Python 3.12+, NumPy, Pillow, `reviewer_support` and the local `arc_repl` runtime on
the import path, plus an explicit `RACKET_PATH`. Tests also work in the review
tool's isolated task-test snapshot, using `reviewer_support.find_root(__file__)`.

`generate_episode(seed, thickness=None)` chooses thickness once from a dedicated
deterministic seed stream and returns a complete private episode plus the Racket
receipt. Passing `thickness=1` or `2` forces a controlled setting for comparisons.
All four input draws use independent named streams, so fixing a seed while
changing thickness preserves the input grids. Every pair in an episode receives
the same program and parameter.

## Input and lesson contract

Each episode contains three demonstrations and one query, with the fourth pair
used as the production query. Every input has exactly two components, with
nonoverlapping bounding boxes: a broad 5–8 by 5–8 component and a narrow 2 by 3–5
component before rotation. One to three blank rows separate them before a global
rotation/reflection. Zero is background; component colors range from 1 to 9 and
may repeat. Broad shapes are connected crosses, hooks, or combs; their occupied
centers make discarding the original shape visible.

These constraints are identical for both parameter settings. Broad boxes ensure
the thickness settings differ and thickness 2 still leaves a hollow interior.
Narrow boxes are a deliberate coincidence: both settings fill their entire bbox.
Narrow-only lessons cannot identify thickness. The focused test records that
ambiguity rather than treating absence of a query error as identification.

The census compares the two declared parameter settings using their actual
Racket outputs, records refuting pair indices, and checks all four choices of a
single held-out query against the remaining three demonstrations. It establishes
identification only against these parameter rivals on these sampled lessons.
It does not certify arbitrary inputs, all seeds, or unrelated shortcut rules.

## Evidence and confidentiality

`racket-executions.private.json` stores every evaluated input, exact program text,
program SHA-256, and actual outputs/receipts from
`arc_repl.isolated_verifier.verify_candidate`. Its one zero-grid canary per
program is execution plumbing, outside every episode. Python only constructs
inputs, validates their geometry, assembles episodes, and compares Racket labels;
it does not synthesize output labels.

`episodes.private.json` contains complete original and alternative episodes at
seed 0. `challenge-a.public.json` and `challenge-b.public.json` are whitelist
projections containing only demonstration inputs/outputs and query inputs.
They omit seeds, parameter values, program/reference code, and query answers.
`report.json` binds the source files and programs to hashes and records canonical
agreement, bounded lesson counts, all rotation verdicts, a distinct-output
witness, and limitations. Public and private files must be distributed separately.

The repository-layout `wrap_rule` smoke failed because its `scripts` import is
only present in the staged layout. The prototype uses the existing public
Racket-only isolated verifier API, which executes the exact `(rule! ...)` source
through `ArcExecutor` and `RacketBridge` without changing shared code. The genuine
failed probe and proposed shared fix are retained in `checks/parametric/commands.json`.
