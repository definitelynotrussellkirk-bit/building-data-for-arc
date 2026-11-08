# Mask-role parameter — task-local prototype

This proposed extension changes which input cells form the self-tiled mask.
It keeps the family’s two-scale conjunction: an output cell is painted only
when both its block source and its subcell source satisfy the **same** selected
predicate. It does not change the selected per-puzzle generator or canonical
Racket authority, and it is not training-admission evidence.

| Parameter | Bounded values | Original/default | Executed change |
|---|---|---|---|
| `mask_role` | `background`, `foreground` | `background` | Select `value == 0` or `value != 0` at both coordinates. |

For an `n × n` input and its sole nonzero color `c`, the output is `n² × n²`.
The default is the canonical zero-mask Kronecker square. The alternative is
the foreground-mask Kronecker square, painted with the same input color.
No second parameter is proposed: this one changes the reasoning while keeping
the original transformation recognizable.

## Inputs and episode contract

Both settings use the selected generator’s unchanged input constraints:
square side 3–5, exactly background 0 plus one nonzero color, at least three
zero cells and at least two foreground cells, with both supports spanning at
least two rows and columns and neither support a solid rectangle. Input
constraints do not depend on `mask_role`.

`make_episode(seed, mask_role="background")` is canonical by default.
An explicit `"foreground"` setting changes the whole episode. For deterministic
setting draws, `mask_role=None` chooses `("background", "foreground")[seed % 2]`
**once before any input draw**. This choice is independent of demonstration or
query count. The same seed produces the same input sequence for either setting.
Inputs use the selected generator at difficulty `medium`, indices starting at
0. The complete evidence episodes have three demonstrations and one query.
The Python API permits 1–8 demonstrations and 1–4 queries; these are prototype
bounds, not a production generation interface.

`emit_racket()` returns an exact, self-contained `(lambda (g) ...)` program.
`execute_racket()` sends it directly to the included public `RacketBridge`;
there is no Python labeling mirror or general rule normalizer. Canonical parity
uses the public `strip_rule_wrapper` helper to extract the known self-contained
canonical lambda. Private records retain the exact emitted and executed text
and SHA-256 hashes.

## Run from the outer extraction directory

Use an interpreter with the packet’s declared NumPy/Pillow dependencies, plus
pytest for tests. These commands select the included offline Racket runtime:

```bash
python3 review.py run python3 generators/4ecf2a93671f/workspace/parametric/mask_role.py --seed 46371 --out ../checks/parametric
python3 review.py run python3 -m pytest generators/4ecf2a93671f/tests/test_parametric_mask_role.py -q
```

If this extraction uses the prepared `WORK/.venv-review`, these concrete
commands select it for both the wrapper and payload:

```bash
WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python generators/4ecf2a93671f/workspace/parametric/mask_role.py --seed 46371 --out ../checks/parametric
WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python -m pytest generators/4ecf2a93671f/tests/test_parametric_mask_role.py -q
```

Output directories must be new; select another `--out` path to replay a
retained run. Payload paths are relative to `WORK/repo/`.

## Evidence and its limits

The authoring command creates exactly three files under `WORK/checks/parametric/`:

- `episodes.private.json`: both complete episodes, their fixed settings, exact
  Racket and executed lambdas/hashes, seed and draw indices, prototype and
  selected-generator source hashes, canonical source identity, direct Racket
  predictions for both declared settings, and finite identifiability results.
- `challenges.public.json`: only demonstration input/output pairs and query
  inputs. It has no parameter values, seed, program, source metadata, or query
  outputs. Give only this file to a solver.
- `verification.json`: actual payload invocation, artifact hashes, repeated
  direct execution of all eight episode labels, compatibility of both settings
  with demonstrations, all four canonical-pair comparisons, generated-input
  canonical parity, and one lawful input with both settings’ differing outputs.

The two role supports are nonempty and disjoint. Their self-products therefore
differ on every lawful input; a correct lawful demonstration distinguishes the
two declared settings before a query needs that distinction. `analyze_settings`
still enumerates both programs by execution and records their actual matching
demonstrations. With no demonstrations, it reports both settings and any query
disagreement as ambiguous; contradictory demonstrations are recorded as
inconsistent. It never uses a hidden query answer to identify the setting.

These checks establish the two declared parameter settings for the recorded
seed and examples. They do not enumerate arbitrary competing programs, prove
all seed distributions, admit model trajectories to training, or change any
approval hash. Prototype tests and evidence are separate from canonical repair
coverage. No shared runtime or catalog interface is modified.
