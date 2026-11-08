# First-marker canopy and parity-lane relay

This is a separate native proposal. The selected production generator remains
version 2.0.0 and its source-bound unresolved column-major teaching audit remains
unchanged. The proposed family addresses that shortcut in its own lessons.

## Executed rules

`{"seed_mode":"first"}` returns the exact selected canonical Racket bytes.
Read the first nonzero cell in row-major order, `(r,c,v)`. Produce a blank grid
of the same dimensions; paint yellow (`4`) in every row through `r`, inclusive,
in columns having the same parity as `c`. Place color `v` at `(r+1,c)` if that
coordinate lies inside the grid. Erase all other input cells.

`{"seed_mode":"parity_relay"}` first finds that same origin. Stage A projects
a mask down every column having the origin column's parity, strictly below the
origin's row. Stage B selects the first row-major original nonzero marker in
that mask. If the mask contains no marker, retain the origin. Apply the canopy
and echo construction using the selected marker's row, column and color.

The input-derived mask is the intermediate consumed by stage B. Ignoring its
parity can select an earlier distractor and change both the canopy and echo.
The retained protected counterfactual witnesses that dependence. This is
contextual gating by a computed mask, not an iterative state simulation. No
rotation/reflection equivariance is claimed: row-major order, downward lanes,
and the upper canopy are part of the task.

## API and grammar

`program(settings)` returns complete `(rule! ...)` source. `generate(seed,
settings, demos=3, queries=4)` returns complete private `train`, `test`, and
`program_solution`. `mirror` is a Python claim implementation; `analyze` returns
the origin, full lane mask, eligible markers, selected target and output.
Native qualification and focused audits execute the labels through protected
Racket rather than relying on Python agreement alone.

The strict semantic grammar is a rectangular list grid with each dimension
1..30, exact integer colors `0,1,2,3,5,6,7,8,9`, and at least one nonzero cell.
Color 4 is reserved for the output canopy. Arbitrary marker counts, adjacent
markers and bottom-row targets are lawful. All-zero inputs are rejected because
the canonical first-marker authority has no empty-scene branch.

Settings contain exactly `seed_mode`. Seeds are exact integers in
`0..2**63-1`; supported demonstrations are **3–6**, and queries independently
range from 1 through 4. Wrong types, booleans used as integers, unknown keys and
unsupported counts are rejected. The default demonstration count is three.

## Why three demonstrations

The original two-demo prototype had correct labels but failed an independent
lesson/query audit. A rightward-only mask, a color-extreme target, and several
bottom-edge interpretations could fit its demonstrations and change queries.
The returned before evidence retains actual generated lessons, protected labels,
a reduced counterexample and the pre-repair sources.

Three mutually exclusive cases are required to expose the relevant branches:

1. A visible echo from a leftward target. Other eligible markers have colors
   below and above the target's color, and later markers distinguish row-major
   order from column order or nearest distance.
2. No eligible target. Same-row markers and lower opposite-parity markers show
   why the rule falls back to the origin.
3. A rightward target on the bottom row. All eligible markers use the origin's
   color; the clipped echo and the failure of color-based eligibility are visible.

The packet expressly allows a narrower supported minimum. Three examples retain
the full query grammar and keep ordinary context near the requested default.
The three core scenes are 12×16, 9×13 and 7×13. A finite demonstration-only cover
selects among at most 64 candidates; failure is explicit. It never inspects a
query or its answer. Additional demonstrations use 7×9, 15×19 and 19×23 profiles.

Four private queries use 5×7, 13×17, 23×27 and 30×30 profiles, shuffled by a
separate seed stream. They include active, fallback and bottom-hit cases, sparse
and dense markers, arbitrary target colors and substantial boundary-reaching
content. Inputs are matched across settings; demo/query count requests are
stable prefixes; each returned input and output is freshly allocated. A bounded
64-attempt duplicate check preserves all requested distinct inputs.

## Reusable evidence tools

`rivals.py` supplies independently authored Python and Racket alternatives and
hand-built controls. `audit.py` checks finite teaching coverage, literal labels,
canonical identity, count prefixes, source stability and dense 30×30 scenes.
Its focused fixture, additive-rival and generated-episode phases avoid repeating
unchanged checks. The separate final-review bank was frozen before it read the
prototype and is retained under `checks/033db13a9d37/final-review/`.

From the outer packet folder, using new output destinations:

```sh
WORK/.venv/bin/python review.py task-tests 033db13a9d37 --phase after --out ../checks/033db13a9d37/task-tests-replay
WORK/.venv/bin/python review.py run python3 generators/033db13a9d37/workspace/parametric/audit.py --episodes-only --out ../checks/033db13a9d37/episodes-replay.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 033db13a9d37 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/033db13a9d37/qualification-replay --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/033db13a9d37/qualification-replay/qualification.json --out ../checks/033db13a9d37/preview-replay
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/033db13a9d37/preview-replay
```

Use the audit CLI help for the retained phase commands and the native manifest
helper before qualification after source edits. Give a consumer only one selected
`preview/public/<hash>.json` at a time. Settings, seeds, reference programs,
answers and all other query inputs remain private. The packet-local
`checks/projection_edges.py` checks the actual saved public views and adversarial
export mutations.

Finite rival/seed checks do not prove universal identification, all-seed success
or measured learning gains. Native reviewer qualification is separate from owner
exact-source acceptance and training admission.
