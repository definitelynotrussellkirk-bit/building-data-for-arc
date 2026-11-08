# Frame-row lookup offset — task-local prototype

**Status: prototype / proposed, not production-approved.** This is a separate
extension of original ARC training family `15660dd6`, task `a61246736c26`.
It leaves the selected `generator.py`, canonical Racket authority, approval
hashes, and production interfaces unchanged.

## Parameter and preserved reasoning

| Parameter | Allowed values | Canonical/default | Effect |
|---|---|---|---|
| `frame_row_offset` | `0`, `1`, `2` | `0` | Each column's solid swatch row `r` selects frame swatch `(r + offset) mod 3`. |

Rows are ordered top to bottom. Offset `1` selects the next row, wrapping the
bottom row to the top. Offset `2` selects the previous row, with the same wrap.
The parameter is selected **once per episode**, before drawing inputs. Explicit
settings are supported; `sampled` uses a seed-keyed `GenCtx` choice and holds it
fixed for every demonstration and query. The normal command defaults to `0`.

Every setting retains the original reasoning steps: parse the color-8 lattice,
locate the one solid swatch in each column, recover its fill color and duplicated
pattern, select a frame color from the leading row-swatch strip, recolor the
pattern, and concatenate the result with color-8 separators. Only the row index
used in the frame lookup changes. The default program is the **exact canonical
program text**, with canonical normalized rule hash `08238424436c`. Alternatives
replace one checked lookup expression; materialization fails if that authority
or the expected expression changes.

Inputs retain the canonical generator's constraints: three row bands; distinct
row-swatch colors `5`, `9`, and `0`; one solid fill and two identical patterns per
column; color-1 frames; color-2 pattern ink; and color-8 separators/background.
This prototype draws medium examples through the existing `generate` and
`self_check` functions. It cycles the stable profiles `row_cycle_012`,
`permuted_frames`, `four_columns_reverse`, and `zero_frame_all`. The input draws
are independent of the offset, so identical seeded inputs can demonstrate that
the parameter changes the executed rule rather than only the input sampling.

The three distinct row swatches and visible frame guarantee that each lawful
example separates all three offsets. Generation still executes every declared
rival and rejects unidentified episodes. Checks include the original train/query
split and each possible leave-one-pair-as-query rotation. These are rotations
of **example roles**, not spatial grid rotations: the original family retains
its oriented leading swatch strip and horizontal output.

## Exact commands

Run these from the extracted packet's `WORK/` directory. The wrapper selects the
included offline Racket and runs the payload from `WORK/repo/`. Use a fresh output
directory for generation and a fresh report path for checking.

```bash
# Three complete episodes: canonical 0 and alternatives 1 and 2, same seed/input draws.
python3 run_with_racket.py python3 generators/a61246736c26/workspace/parametric/prototype.py generate --seed 1701 --all-settings --out ../checks/parametric/evidence

# Replay the exact retained programs/outputs and recheck source hashes and public projection.
python3 run_with_racket.py python3 generators/a61246736c26/workspace/parametric/prototype.py check --bundle ../checks/parametric/evidence --report ../checks/parametric/check.json

# Focused prototype tests only; canonical repair tests are a separate scope.
python3 run_with_racket.py python3 -m unittest discover -s generators/a61246736c26/tests -p test_parametric_a61246736c26.py -v

# A single canonical-default episode.
python3 run_with_racket.py python3 generators/a61246736c26/workspace/parametric/prototype.py generate --seed 29 --out ../checks/parametric/example-default

# A single episode whose rule is chosen deterministically once from its seed.
python3 run_with_racket.py python3 generators/a61246736c26/workspace/parametric/prototype.py generate --seed 29 --frame-row-offset sampled --out ../checks/parametric/example-sampled
```

The last two commands are usage examples, not claims of retained execution.
Outside the review packet, the same payload works from the repository with
Python plus the repository's shared runtime on `PYTHONPATH` and the supported
Racket executable available through `RACKET_PATH`. For the direct repository
layout, the prototype maps the legacy `scripts` import namespace to the existing
`shared/tools` directory so shared `wrap_rule` can load its parser. The relocated
runtime already provides that namespace. No runtime copy is made.
`prototype.py --help`, `generate --help`, and `check --help` describe all options.

## Outputs and evidence boundary

Give a solver **only** `public/episode-NNN.json`. Each public file contains just
`train` pairs with `input`/`output` and `test` pairs with `input`. It omits seed,
parameter values, rule/program text, provenance, and query answers. Public
filenames use neutral sequence indices. Do not give the solver the containing
evidence directory: its other files are private authoring material.

`private.json` retains the deterministic seed, selected parameter per episode,
source SHA-256 hashes, exact materialized Racket text and hashes, runtime identity,
input draw profiles, executed outputs for **all** three rivals, canonical-example
execution checks, distinguishing witness, and train/query identifiability reports.
`programs/frame-offset-N.rkt` materializes each exact rule separately.
`manifest.json` binds the evidence files and records the actual payload command
and working directory. `check.json` records a new Racket replay, counts, runtime
identity, source hashes, and evidence hashes. All example labels are produced by
the shared `RacketBridge` using shared `wrap_rule`; a Python mirror does not
supply labels. The bridge is explicitly closed after use.

With the default counts, the retained all-settings bundle contains three
complete episodes of three demonstrations and one query. Four input grids are
shared across settings. Each generate/check run executes 12 parameter/input
combinations plus the three recorded canonical examples: 15 rule applications.
The report checks six episode/alternative-rival comparisons and twelve query
role rotations. The complete output grids, not just pass flags, are retained.

The evidence is bounded to its recorded seed and profiles. It distinguishes the
three declared offsets; it does not prove uniqueness among every conceivable
ARC transformation, broad seed coverage, or production training admission.
Canonical repair approval does not approve this extension.
