# Mirror concatenation: proposed task-local prototype

This separate prototype extends task `2c30a4753f6b`, family
`training:c9e6f938`, with two small rule parameters. It does not change
`generator.py`, selected Racket authority, catalog metadata, approval, or the
production generation interface.

| Parameter | Allowed values | Default | Executed effect |
|---|---|---|---|
| `axis` | `horizontal`, `vertical` | `horizontal` | Reflect left/right and double width, or reflect top/bottom and double height. |
| `side` | `after`, `before` | `after` | Put the reflected grid after or before the original along the chosen axis. |

The default preserves the original grid as the left half and appends its
left/right reflection. The other settings preserve the whole-grid copying,
reflection, and seam relationship. No objects are extracted, recolored, or
discarded. Horizontal inputs have height 1..30 and width 1..15; vertical inputs
have height 1..15 and width 1..30. Colors must be literal integers 0..9, and grids
must be nonempty and rectangular. Thus every output is at most 30 by 30.

## Runnable commands

Run from the outer extraction directory containing `review.py`. The wrapper
selects the included offline Racket runtime and runs payloads from `WORK/repo`.
Python 3.12+, NumPy, Pillow and pytest are needed for the full focused tests.

```bash
python3 review.py run python3 generators/2c30a4753f6b/workspace/parametric/reflection.py emit --all-settings --seed 20261023 --out ../checks/parametric/episodes
python3 review.py run python3 generators/2c30a4753f6b/workspace/parametric/reflection.py verify ../checks/parametric/episodes --out ../checks/parametric/verification.json
python3 review.py run python3 -m pytest -q generators/2c30a4753f6b/tests/test_parametric_reflection.py
```

If dependencies are installed in the review virtual environment, use the same
interpreter for both wrapper and payload:

```bash
REVIEW_PY="$PWD/WORK/.venv-review/bin/python"
"$REVIEW_PY" review.py run "$REVIEW_PY" generators/2c30a4753f6b/workspace/parametric/reflection.py emit --all-settings --seed 20261023 --out ../checks/parametric/episodes
```

Choose a fresh output path for each run: existing paths are refused. To emit a
single episode, omit `--all-settings`; explicit `--axis vertical --side before`
selects that setting. Use `--axis sample --side sample` to choose the parameters
once from the seed. With no parameter flags the default is horizontal/after.
Seeds are literal integers in 0..2**63-1. The Python API exposes the same bounded
`Settings`, `sample_inputs`, `program`, `emit_bundle`, and `verify_bundle` methods.

## Episode construction and identifiability

Every episode has exactly three demonstration pairs and one query. One setting
is held fixed across all four. Input draws use a local deterministic RNG and
never touch global RNG state. Given a seed, all settings use the same inputs.
Demonstrations vary dimensions and sparse, intermediate, or dense colored
content. Four distinct corner colors construct both-axis asymmetry without
unbounded rejection sampling. Each demonstration independently separates all
four settings. The query has strictly more rows and columns than every demo;
its dimensions remain at most 15 by 15, so all declared rivals are also lawful.

The tiny 2 by 3 `distinct_setting_witness` additionally records four different
executed outputs on one common input. The prototype checks every other declared
setting on every demonstration and query. A surviving rival that changes the
query is labelled `ambiguous_query`; no such result is silently called a pass.
These checks cover the declared four-setting family and recorded seeds. They
are not a proof against every plausible program.

## Public data and private execution evidence

Only files under `public/` are model-visible challenges. Their sole top-level
keys are `train` and `test`; demonstrations contain input/output grids and the
query contains only its input. Filenames are opaque. No parameters, seed,
reference code, query label, or authority metadata is included in those files.

`private/evidence.json` retains parameters, seed, prototype/test/document hashes,
all exact Racket programs and hashes, executed labels, every alternate-setting
prediction and score, the common witness, counts, and the Racket runtime
identity. `private/rules/*.rkt` materializes the exact four rule payloads; these
are DSL expressions used by the bridge, not standalone `#lang` modules.

The protected `RacketBridge.eval_text` method executes each exact program in a
lexical adapter that returns the callable registered by `rule!`, then applies it
to the quoted input. Cached values come only from successful real Racket
execution. A separate Python implementation checks parity but never creates the
labels. `Catalog.apply(..., reference="canonical")` independently executes the
selected production authority on all four sampled inputs and the witness. Its
normalized authority identity and all five outputs must match the default.

`verify` checks current source bindings, fixed semantic metadata, all saved
program files, the complete public file inventory, and public redaction/content.
Canonical JSON comparisons distinguish Boolean/float cells from integer cells.
It then reexecutes every selected and rival output plus the witness, reruns
canonical parity, and compares input/output and authority hashes. The original
runtime metadata remains a historical receipt; verification records its own
current protected Racket identity and reports comparisons of binary, bridge,
prelude, and symbol-policy hashes. A runtime byte difference is reported rather
than treated as a label mismatch; machine paths are not compared. Verification
output also requires a new path outside the bundle's `public/` directory. A failed emission retains
`private/failure.json` and refuses to overwrite that directory on retry.

Focused tests are prototype coverage, separate from canonical repair coverage.
They include malformed values, axis-specific dimension bounds, deterministic
fresh returns, all-setting separation, real Racket execution, public redaction,
overwrite refusal, and tamper rejection. Emitted evidence records actual finite
counts; passing it does not approve the proposed variants or admit trajectories
to training.
