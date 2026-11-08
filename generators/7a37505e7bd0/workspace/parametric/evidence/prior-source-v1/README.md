# Bounded color-count expansion prototype

**Status: proposed, task-local prototype.** This directory does not change the
selected generator API, canonical Racket authority, approval hashes, or training
admission. Canonical production repair and this extension have separate tests
and evidence. The source and task-test files can travel in the existing
task-workspace patch scope.

## Rule and parameter domain

The original task counts distinct colors and makes a block from every input
cell. Both parameters retain that reasoning: determine which colors count,
compute one factor, then repeat each original cell along the selected axes.
Zero-colored cells remain in the grid under either counting policy.

| Parameter | Allowed values | Meaning |
|---|---|---|
| `counting_policy` | `all_colors`, `nonzero_colors` | Count all distinct colors, or count only distinct colors unequal to zero. |
| `expansion_axis` | `both`, `rows`, `columns` | Repeat rows and columns, rows only, or columns only. |

The original/canonical setting is **`all_colors`, `both`**, exposed as
`CANONICAL_PARAMETERS`. Its materialized Racket source is the exact selected
canonical source, not a relabeled alternative. There are exactly six settings.
For the other settings, the executed scale factor is `max(1, counted_colors)`.
Rows-only expansion makes each cell an `n × 1` block; columns-only expansion
makes each cell a `1 × n` block. Factor one gives identity for all three axes.

Inputs use the selected task generator's existing lawful 3×3 teaching domain:
one through five colors, the existing frequency bounds and canonical exceptions,
and the existing palette/layout roles. Generated monochrome inputs use color
3 or 8, so every emitted input contains a nonzero color and the counted factor
is at least one for both policies. All-zero grids, arbitrary shapes, and inputs
rejected by that generator's `self_check` are outside this prototype's domain.
The `max(1, ...)` guard keeps the emitted expression defined; it does not widen
the accepted input domain. No parameter changes input sampling constraints.

The module dynamically loads the selected generator from its own checkout.
It calls `generate(seed, sample_start + offset, difficulty=band)` for offsets
0 through 5 with no sampling overrides. The first five pairs are demonstrations
and the sixth is the query. This preserves the original count schedule, including
zero in the count-two and count-four inputs, identity examples, non-modal 3/8
witness roles, and easy/medium/hard layouts. `sampling.base_observables` retains
the original sampler's observations; its `output_shape` describes the canonical
sampler rule. The actual variant output is the separately retained Racket label.

Omitting explicit parameters selects one complete setting deterministically from
the episode seed: SHA-256 of the documented schema/seed string, interpreted as a
big-endian integer modulo six in the declared setting order. The selection does
not depend on sample index, difficulty, input contents, or global Python RNG.
The same selected values label every demonstration and query. Explicit settings
are supported for bounded verification; both values must be provided together.
Seeds and sample starts are nonnegative integers excluding booleans, and the
difficulty must be `easy`, `medium`, or `hard`.

## Racket execution and information boundary

`rules/` contains the exact six materialized `(rule! (lambda ...))` programs.
These are programs for the included ARC Racket bridge and prelude, not standalone
`#lang racket` modules. All six are closed lambda expressions without shorthand
forms or free `h`/`w` variables. The existing `strip_rule_wrapper` helper extracts
their callables; the general shorthand wrapper needs a staged `scripts` namespace
that the direct authoring command does not install. No generic parser or shared
runtime code is copied or changed here.

`RacketOracle` defines and executes the materialized callable using the included
`RacketBridge`. It never computes output grids with a Python mirror. Its cache
stores only actual Racket executions keyed by exact program and input hashes.
Query rotations reuse those real labels and draw no new inputs. The evidence
records both the `(rule! ...)` text/hash and executed callable text/hash, the
bridge expressions, input/output grids and hashes, runtime identity, current
prototype/support/generator source hashes, and sampling indices. A final source
comparison detects changes during a run. The canonical comparison executes the
selected reference separately on all eight canonical labeled pairs and compares
both results with the retained canonical labels.

Only `public/*.json` is model-visible. A public challenge contains exactly
`train` inputs/outputs and one `test` input. It has no parameters, seeds, source,
program, query output, or query-output shape. Public filenames are opaque episode
numbers. `private/episodes/` contains full episodes and separate receipts with
the exact parameters, seeds, source/program hashes, program text, and Racket
outputs. Keep the full report, rival evidence, and all other `private/` files with
the authoring controller.

## Demonstration checks and controls

Every episode compares its demonstrations with **all five other parameter
settings**, using their executed Racket labels. A generated episode is accepted
only when every other setting is refuted by a demonstration. Scoring separates
`refuted`, `survived_all` (same demos and same query), and `ambiguous` (same demos,
different query). Supplied labels that disagree with the chosen Racket program
raise an error before rival scoring.

The evidence command holds out each of the six existing labeled pairs once,
leaving five demonstrations in their original order. Each record retains the
real query index, demonstration indices, all rival statuses and mismatch
indices, and references/hashes for executed rival predictions. Rotation counts
include the original query position and are not independent draws.

The common-input witness is generated with seed 17, sample index 1, medium
difficulty. It contains four colors including zero and is lawful under the
original sampler. On that exact same input, the six settings yield respectively
12×12, 12×3, 3×12, 9×9, 9×3, and 3×9 outputs. Full cells and program hashes are
retained in `private/difference-witness.json`.

The negative control deliberately selects lawful zero-free demonstration inputs
with seed 17 and indices `[0, 2, 3, 5, 7]`, then uses the zero-containing input at
index 1 as query. All labels come from canonical-setting Racket execution. The
`nonzero_colors`, `both` rival fits the demonstrations and disagrees on the query.
This is an intentionally incomplete demonstration selection, not a complete
emitted episode. It is retained as measured ambiguity, with **zero solver
attempts**. No solve predictions, synthetic solver histories, or independent
human-identification claims are manufactured.

## Exact commands from the outer packet directory

Run these from the directory containing `review.py` and `WORK/`. The wrapper
selects the included offline Linux x86_64 Racket executable and sets the payload
working directory to `WORK/repo/`. The packet's `WORK/.venv` supplies pytest,
NumPy, and Pillow. Use fresh evidence output directories when replaying.

```bash
# Re-materialize all six task-local source programs.
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/7a37505e7bd0/workspace/parametric/prototype.py materialize \
  --out generators/7a37505e7bd0/workspace/parametric/rules

# Focused prototype integration tests, including actual Racket execution.
WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest -q \
  generators/7a37505e7bd0/tests/test_parametric_7a37505e7bd0.py \
  --basetemp=../checks/parametric/final-tests-tmp

# One setting chosen once by episode seed, with public/private separation.
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/7a37505e7bd0/workspace/parametric/prototype.py episode \
  --seed 17 --difficulty hard --sample-start 3 \
  --out ../checks/parametric/seeded-episode

# Explicit original setting; the two parameter flags must be supplied together.
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/7a37505e7bd0/workspace/parametric/prototype.py episode \
  --seed 17 --difficulty medium --sample-start 0 \
  --counting-policy all_colors --expansion-axis both \
  --out ../checks/parametric/explicit-episode

# All six settings × three bands × four seeds × two starts:
# 144 complete episodes, 864 labeled pairs, and 864 query rotations.
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/7a37505e7bd0/workspace/parametric/prototype.py evidence \
  --seeds 0 1 2 17 --bands easy medium hard --starts 0 3 \
  --out ../checks/parametric/final
```

`python3 review.py run ../.venv/bin/python ...` is the equivalent outer dispatch
when `python3` can run the packet's standard-library-only wrapper. From `WORK/`,
the equivalent entry point is `.venv/bin/python run_with_racket.py
../.venv/bin/python ...`; its payload still starts in `WORK/repo/`.

`materialize` exits zero after writing source only and does not claim execution.
`episode` executes all labels and parameter rivals before exporting.
`evidence` exits zero only when its recorded bounded checks pass, including the
expected ambiguous negative control; failure remains visible in its report.
Read `report.json` for actual counts, source hashes, command, runtime, file
digests, per-episode records, and limitations. Outer command/stdout/exit receipts
are retained beside the evidence directories by the reviewer.

## Verification scope and limitations

The prototype test file covers canonical Racket parity, all six actual block
expansions, strict parameter/domain validation, seeded determinism and fresh
returns, preserved base inputs, complete episodes across bands/seeds, all query
rotations, tampered-label rejection, the ambiguity control, and export leakage.
The expected initial TDD failure log is `WORK/checks/parametric/tdd-red.log`.
`first-green.log` retains the subsequently diagnosed direct-layout wrapper
dependency failure. Final focused test results and the full bounded matrix are
retained under `WORK/checks/parametric/`; canonical repair checks remain separate.

This is finite evidence against the five other declared parameter settings.
It does not prove identification against every plausible rival, every seed, or
every possible input. In particular, the original sampler's frequency-template
restriction remains unchanged; a production histogram-based shortcut can fit
its generated templates even though canonical data refutes that shortcut.
Those broader canonical teaching-distribution findings belong to the main
review and are not resolved by successful parameter-setting discrimination.
No general production parametric API, catalog-kind change, training admission,
model evaluation, or approval for the five alternative rules is included.
