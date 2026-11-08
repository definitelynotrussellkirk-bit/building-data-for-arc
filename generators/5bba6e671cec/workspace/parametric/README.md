# Proposed parametric prototype: whole-color centroid rotation

This is a task-local **prototype**, with no production approval or training
admission. The canonical `generator.py`, catalog and reference authority remain
selected as before. Inputs are produced by that generator without overrides;
all grids remain 8×8. No size-generalization claim is made.

## Bounded rule parameters

| Parameter | Values | Canonical default |
|---|---|---|
| `direction` | `cw`, `ccw` | `cw` |
| `steps` | integer `1`, `2` | `1` |

Every nonframe color, including zero and disconnected occurrences, remains one
semantic region. Order whole-color centroids around the grid center. Preserve
all 4 and 7 cells; move each color clockwise or counterclockwise by the selected
number of positions. Input constraints do not depend on these parameters.
`instantiate_rule()` returns the exact canonical Racket bytes at `cw1`; the
other settings replace only the authority's single mapping-offset literal.

`choose_setting(seed)` chooses one setting using a fixed SHA-256-derived index.
`make_episode()` calls it once, before generating any pair. The same setting
labels three demonstrations and one query. An explicit setting argument exists
for authoring tests; CLI evidence uses ordinary seed selection. To exercise all
four settings reproducibly, each audit `--seed` denotes a 1024-seed stratum. The
audit finds the first seed in that stratum selecting each setting, records both
the requested stratum and actual seed, then generates the episode normally.
The bounded search fails visibly if a setting has no seed in its stratum.

## Reusable CLI

From the packet extraction root, replacing the absolute interpreter path if the
packet was relocated:

```sh
WORK/.venv/bin/python review.py run /absolute/WORK/.venv/bin/python generators/5bba6e671cec/workspace/parametric/rotation.py audit --out /absolute/WORK/checks/parametric/audit
WORK/.venv/bin/python review.py run /absolute/WORK/.venv/bin/python generators/5bba6e671cec/workspace/parametric/rotation.py rescore --input /absolute/WORK/checks/parametric/audit --out /absolute/WORK/checks/parametric/rescore.json
WORK/.venv/bin/python review.py run /absolute/WORK/.venv/bin/python -m unittest discover -s generators/5bba6e671cec/tests -p 'test_parametric*.py'
```

The payload runs in `WORK/repo`. A direct relocated checkout can instead run
`rotation.py` using its local dependencies with a protected Racket runtime on
PATH or in `RACKET_PATH`. No predecessor checkout is imported. The prototype
locates its own repository and uses its `shared/runtime` bridge and helpers.
Python, NumPy, Pillow and Racket are the ordinary repository dependencies.

Default audit population: all four settings, seed strata 0/1/2, all three
explicit difficulty bands, and consecutive starts 0/1/2/3: **144 episodes,
576 pairs, and 576 single-query holdouts**. Repeat `--seed`, `--band` and
`--start` to define a smaller or additional population. Each start uses exactly
four consecutive production indices; there is no rejection/resampling policy
silently changing the requested population.

The CLI executes every setting's exact Racket program on every episode input
and compares those results with the diagnostic Python predictions. Selected
Racket outputs alone supply labels. It also checks every labeled canonical
pair at `cw1` and retains six pairwise setting witnesses. The source hashes,
materialized Racket programs, rule hashes, actual seeds and sample indices,
complete selected inputs/outputs and all finite-rival scores are retained.

`public/challenges.jsonl` contains only demonstration input/output pairs and
query inputs. Its row order matches the private episode list. Keep the entire
`private/` directory and `manifest.json` with the author/controller; these contain
hidden settings, query answers and reference programs. Public files contain no
settings, seeds, reference code or query labels. Do not hand the whole evidence
directory to a solver.

`rescore` validates asset/source hashes, exact rule text, canonical authority,
input regeneration, seed selection, public/private projection, all stored Racket
labels and pairwise witnesses, then recomputes every rival score. Changing the
selected source invalidates its receipt; create fresh evidence after a change.
Output directories/files must be new. Exit **0** means no measured ambiguity or
execution error under the selected policy; **1** means measured ambiguity or a
missing setting witness; **2** means execution, integrity or validation failure.
Errors are printed as structured JSON on stderr. Source changes during an audit
are rejected. An incomplete run must never be cited as passing evidence.

## Discrimination and limits

The probe iterates the live `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS` and
`LESSON_COMPETITORS` registries and binds each declared name to an explicit
adapter; a new unsupported declaration fails visibly. At the canonical default,
every adapter is checked against its live callable on every episode input.
Per-setting namespace/name/adapter bindings are retained in private evidence.
The live counterclockwise rival is covered by the opposite-direction parameter
setting at the selected step count.

Rivals include all four parameter settings, numeric-color order, row-major
first occurrence order, first-cell centroid angle, fixed quadrant order,
zero-as-background, rotating frame colors, and identity. Shortcut rules use the
selected episode's direction and step count. The selected parameter setting is
included as a positive control. This is finite-rival evidence, not proof that
no other rule fits.

Modulo aliases matter: clockwise/counterclockwise one-step rules coincide with
two regions; both two-step rules are identity with two regions and coincide
with four regions; `cw1=ccw2` and `ccw1=cw2` with three regions. Therefore no
single palette size can distinguish all four settings. Mixed palette lessons
must refute a rival before a query needs that distinction. The scorer records
`refuted`, `survived_all`, or `ambiguous`; an everywhere-equivalent surviving
rival is not mislabeled as query ambiguity.

Production uses the first three pairs as demonstrations and the fourth as its
query. Every one-pair holdout is also scored. These verdicts are recorded
separately. `--rotation-policy require` is the default and fails if any holdout
is ambiguous. `--rotation-policy diagnostic` records every such finding while
requiring only the production lesson to pass. Neither policy changes the input
schedule or hides failures.
