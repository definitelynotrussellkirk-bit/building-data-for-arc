# Proposed `stroke_symbol` prototype

This is a separate, runnable authoring prototype for task `a61246736c26`
(original family `training:15660dd6`). It does not change the canonical
per-puzzle API or approve a variant for production.

## Bounded rule parameter

| Parameter | Allowed settings | Canonical/default | Executed change |
|---|---|---|---|
| `stroke_symbol` | Literal integers `2`, `8` | `2` | Replace the chosen symbol inside each extracted pattern tile with its solid tile's fill color. Preserve the other symbol. |

At setting `2`, the exact selected canonical Racket text is returned unchanged.
Setting `8` changes its single `(hash 1 frame 2 fill)` mapping to
`(hash 1 frame 8 fill)`. The prototype checks the canonical normalized rule hash
`08238424436c` and requires exactly one such mapping. A changed authority requires
reassessment; there is no silent fallback or authority replacement.

Both settings retain the same reasoning: find the full color-8 separator lattice;
identify each column's duplicated pattern and solid tile; use the solid tile's
row to select a frame color from the leading swatches; obtain the fill from the
solid interior; emit one recolored pattern per column. Frame recoloring and the
inserted color-8 separators are unchanged. The alternative paints the pattern's
negative space while preserving its 2 cells.

No input constraint depends on the parameter. Canonical pattern tiles contain
both 2 and 8, their frame is 1, row swatches are 5/9/0, and solid fills are among
3/4/6/7. Thus every lawful labeled input distinguishes the two settings: at an
interior 2 cell the alternatives yield fill versus 2, and at an interior 8 cell
they yield 8 versus fill. This is a reasoning argument over the declared domain;
the retained evidence checks a finite population using actual Racket labels.

## Episode policy

`setting_from_seed(seed)` makes one keyed `GenCtx.draw_choice` draw using prototype
version `1.0.0`, task key `a61246736c26_parametric`, sample index 0, and label
`stroke_symbol`. `generate_episode` calls it once, before generating inputs, and
reuses that value for all three demonstrations and the one query. Difficulty
does not enter the parameter draw. The default evidence seeds are 0 (setting 8)
and 1 (setting 2); each is evaluated at easy, medium, and hard difficulty.

Inputs come from the selected canonical generator with these explicit profiles,
in this order: `row_cycle_012`, `permuted_frames`, `four_columns_reverse`,
`shared_pattern`. The seed stays fixed within an episode; sample indices are
0, 1, 2, and 3. Every input must pass that generator's `self_check`, and duplicate
inputs within an episode are rejected. This intentionally bounded authoring
curriculum is separate from canonical production distribution evidence.

The first three pairs are demonstrations; the last is the query. Both declared
settings are run on every input. The selected setting supplies all labels, and
the other setting is scored as a rival. Each of the four labeled pairs is also
held out once while the other three remain demonstrations in their original
order. This checks all single-query rotations of each retained episode against
these two parameter settings. It does not test every possible ARC hypothesis,
variable demonstration counts, multiple simultaneous queries, or all seeds.

## Run from the outer packet extraction directory

The packet's prepared Python environment must include its normal test/runtime
dependencies. The public wrapper selects the included offline Racket runtime.
The output directory must be new; earlier evidence is never overwritten.

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/a61246736c26/workspace/parametric/prototype.py \
  --seed 0 --seed 1 \
  --out ../checks/parametric/final-f6be-evidence
```

To use another bounded population, repeat `--seed` and/or `--difficulty`
(`easy`, `medium`, `hard`). A batch that omits either declared setting is retained
as `prototype_incomplete_or_failed` and exits 1. This is an evidence-coverage
condition; it does not mean the omitted setting is unsupported.

Focused tests, again from the outer extraction directory:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest \
  generators/a61246736c26/tests/test_parametric_extension.py -q
```

The tests cover exact default authority, strict parameter validation, literal
expected outputs on a hand-built lawful witness, all canonical labels, seeded
selection, complete-episode replay, all declared rivals and holdouts, independent
label ownership under mutation, artifact hashes, and clean public challenges.
These are prototype tests; canonical repair/admission checks remain separate.

## Execution and evidence

`prototype.py` uses public `arcpuzzles.runtime.prepare_runtime` to create a
transient task runtime. It launches the included task-local `racket_worker.py`
in that directory. The worker uses the supplied `puzzle_generators.rule_wrap`
normalizer and `arc_repl.racket_bridge.RacketBridge`. It does not calculate labels
with a Python rule mirror. Exact wrapped callables are retained alongside each
materialized source program; source and Racket binary hashes are recorded.

The evidence directory contains:

- `report.json`: parameter contract, source hashes, seeds, settings, metrics,
  declared limits, and a SHA-256/size manifest for every other artifact.
- `programs/`: exact Racket source and its executed wrapped callable for both
  settings. Files intentionally have no extra trailing newline beyond the source.
- `private/episode-*.json`: complete labeled episodes, selected parameters,
  exact source/callable hashes and text, sampling provenance, all executed
  candidate predictions, and every rival/rotation result.
- `public/challenge-*.json`: only `train` input/output pairs and `test` inputs.
  Hidden parameters, rules, seed metadata, and query answers are omitted.
- `canonical-default.json`: all selected canonical labels compared with the
  default setting's Racket outputs.
- `distinguishing-input.json`: one lawful canonical input and both settings'
  different Racket outputs.
- `execution-receipts.json`: actual worker argument arrays, temporary working
  directories, exit codes, runtime/request/output hashes, and stderr. These
  temporary runtime directories are not needed to read the retained labels.

The outer authoring commands, stdout, stderr, real development failures, and
final test results are retained separately under `checks/parametric/`. An initial
v4.0.0 generator snapshot remains distinct from evidence rerun against the final
canonical generator bytes. The successful JSON verdict means only that the
specified finite prototype checks passed; it does not establish production
approval or universal identifiability.
