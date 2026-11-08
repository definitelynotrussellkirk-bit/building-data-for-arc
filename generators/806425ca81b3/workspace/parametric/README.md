# Row/column anchor thresholds — prototype

This is a task-local, unapproved extension of generator `806425ca81b3`, original
ARC training task `22168020`. It does not change the selected generator, its
canonical Racket rule, the catalog, approval, or production runtime interfaces.

## Parameters and invariant reasoning

| Parameter | Allowed values | Canonical/default |
|---|---|---|
| `axis` | `"row"`, `"column"` | `"row"` |
| `min_anchors` | integer `2`, integer `3` | `2` |

For each line on the chosen axis, consider every nonzero color independently.
If it appears at least `min_anchors` times, fill zero cells strictly between its
first and last anchors. Preserve every existing nonzero cell and the grid shape.
This keeps the anchor/background roles, same-color grouping, interval relation,
zero filling, and independent-line composition. The parameters change the
executed axis or threshold rather than merely changing the sampled inputs.

Both parameters are fixed for all pairs in an episode. The default API and CLI
setting is canonical. `sample_parameters(seed)` (or `--sample-parameters`) draws
one setting from a separate deterministic stream; `make_inputs` never resamples
it. Explicit settings allow all four choices to be tested with the same seed.
Unknown parameter keys, booleans, noninteger thresholds/seeds, and unsupported
values are rejected instead of being coerced.

`materialize_rule()` returns the exact selected canonical rule bytes for the
default setting. Every alternative returns its own complete Racket rule. All
labels and rival predictions are executed using the public runtime preparer,
the shared `wrap_rule` normalizer, and the included real `RacketBridge`.
The Python mirror is only a parity check.

## Input and episode scope

Teaching inputs have dimensions 6..30, background 0, and integer colors 1..9.
Every active line on the chosen axis has a repeated color; repeated-color spans
in that line are disjoint. Different-color singletons are permitted, including
inside another color's span. At least one qualifying span has a zero to fill.
These constraints are evaluated relative to `axis` and `min_anchors`; two-anchor
spans remain lawful under threshold 3 but do not fill.

The deterministic sampler creates three demonstrations (8×12, 10×15, 12×18,
transposed for column settings) and one 30×30 query. The query contains 24 active
lines, long spans, two- and three-anchor groups, disjoint multi-color spans, and
singleton distractors. It is not a small grid padded to 30×30.

Every episode checks all three other parameter settings against every labeled
demo and query. It refuses an episode unless the demos uniquely identify the
selected setting within this four-rule inventory. Rival predictions are retained
in private evidence. General well-formed grids outside the sampled grammar are
also executable: overlapping spans use the canonical Racket convention that
the lowest qualifying color wins. The mirror matches that convention.

## Run

From the outer extracted packet directory, with Python 3.12+, NumPy, Pillow,
and pytest available. `review.py run` selects the included offline Racket runtime
and sets the repository import paths. These are the exact authoring commands
(the temporary authoring environment is `WORK/.venv`; substitute another Python
with these dependencies when replaying):

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/806425ca81b3/workspace/parametric/verify.py verify \
  --seed 20261023 --out ../checks/parametric/final

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 WORK/.venv/bin/python review.py run ../.venv/bin/python \
  -m pytest generators/806425ca81b3/tests/test_parametric_806425ca81b3.py -q
```

For one explicit episode, or a setting sampled once from its seed:

```bash
python3 review.py run python3 generators/806425ca81b3/workspace/parametric/verify.py \
  episode --seed 17 --axis column --min-anchors 3 --out ../checks/parametric-example

python3 review.py run python3 generators/806425ca81b3/workspace/parametric/verify.py \
  episode --seed 17 --sample-parameters --out ../checks/parametric-sampled
```

The episode command writes private `episode.json` and public `challenge.json`.
Do not give the private file to a solver. The public projection contains only
`train` input/output pairs and `test` input grids; it omits parameters, seeds,
reference programs, rival predictions, and query outputs.

The verification command writes only two JSON files:

- `WORK/checks/parametric/final/evidence.json`: all four private episodes, exact rules
  and SHA-256 hashes, source hashes, runtime identity, actual command, canonical
  pair checks, a common lawful counterfactual producing four different answers,
  replay checks, query workload counts, and limits.
- `WORK/checks/parametric/final/public_challenges.json`: the four public challenges,
  in a deterministic shuffled order. Its private index mapping stays in evidence.

The retained focused test log is `WORK/checks/parametric/final/tests.log`.
`WORK/checks/parametric/final/commands.json` retains exact commands and exit codes.
The earlier files directly under `checks/parametric/` are superseded development
evidence bound to earlier source bytes; use the `final/` receipt for this version.

## API

`prototype.py` exposes `validate_parameters`, `sample_parameters`,
`materialize_rule`, `make_inputs`, `input_errors`, `mirror`,
`generate_episode(seed, parameters=None, *, runtime=None)`, and
`public_challenge(episode)`. For repeated authoring calls, use
`with reference_runtime() as runtime` and pass that runtime to `generate_episode`.
Call `materialize_rule(setting)` to obtain an exact standalone rule string.

## Limits

This is finite prototype evidence for four settings at one retained seed, plus
focused regression cases. Parameter-rival identifiability does not establish
uniqueness against arbitrary alternative rules or across every possible seed.
The sampler intentionally uses a small discriminative input grammar. It does
not claim a broad distribution, production parameter support, training
admission, or approval of any variant. Canonical repair checks are separate.
