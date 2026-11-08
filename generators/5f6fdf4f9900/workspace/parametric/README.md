# Component priority for concave-corner enlargement

Native authoring adapter for `5f6fdf4f9900`; Python 3.12+, the repository runtime,
and Racket are required. `promotion.json` declares the native contract.

## Rule and admitted grammar

The episode-fixed parameter is `corner_priority`:

| Value | Selection at each empty input cell |
|---|---|
| `scan` (default) | First eligible diagonal neighbor in NW, NE, SW, SE order. `program()` returns the selected canonical Racket text byte-for-byte. |
| `largest_component` | Eligible neighbor belonging to the largest same-color, four-connected component; equal areas use the same directional order. |

Eligibility still requires a nonzero diagonal neighbor and two empty intervening
orthogonal cells. Every input cell expands by the number of distinct nonzero
colors. Foreground becomes solid blocks; the chosen neighbor determines the
red main/anti diagonal in an empty block. Other empty blocks stay empty.

The separate parametric grammar allows disconnected occurrences of a color.
Inputs have 2–5 nonzero colors, zero background, and no red input cells; each
dimension is 4–15 and each enlarged dimension must be at most 30. The canonical
generator's own distribution and source are unchanged. A 30×30 input is unlawful
here because the minimum enlargement factor two would exceed the output limit.

The fourth query alternates by seed between populated 6×6 inputs with five
colors and populated 15×15 inputs with two colors, both yielding 30×30 outputs.
Other queries cover 4×4, 5×6 and 6×5 inputs, with scales two, three and four.
The larger inputs contain region growth and disconnected pieces, not empty
padding. All input draws are independent of the selected private setting.

## Teaching and actual dependency

Two constructive demonstrations distinguish the finite settings. The first
separates component area from whole-color frequency and contains opposing
candidate orientations and ties. The second distinguishes four-connectivity,
bounding-box area, ignored orthogonal blockers and smallest-component selection.
Its singleton was moved after a live Racket audit found a smallest-component
shortcut fitting the initial canonical demonstrations. The repair adds no demo.

The dependency is: compute the same-color four-connected components and their
areas → bind each eligible corner to its component area → choose the largest
eligible neighbor and paint its orientation. Remote cells can change the
winning direction while the entire local 3×3 corner neighborhood stays fixed.
The causal receipt compares the alternate program with the exact scan program
that skips the area decision. It is finite execution evidence, not a universal
proof of learnability or measured training benefit.

`generate(seed, settings, demos=3, queries=4)` supports 2–6 demonstrations and
1–4 queries independently. Four novel queries are the normal request. The first
two demos use different scales (three and four); later demos are sampled.
`teaching_check()` identifies the setting using demonstration labels only.
The separate audit tests ten declared executable wrong rules per setting.

## Run from an extracted packet

Use the same passing interpreter as `review.py python-check`; the commands
below use the packet's local venv. Choose new output paths for every fresh run.

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/5f6fdf4f9900/workspace/parametric/audit.py \
  --out ../checks/5f6fdf4f9900/self-audit-fresh

WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/5f6fdf4f9900/tests/test_parametric_corner_priority.py \
  generators/5f6fdf4f9900/tests/test_parametric_export.py -q

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  5f6fdf4f9900 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/5f6fdf4f9900/qualification-fresh --summary
```

The audit retains complete private episodes, all exact executed programs, a
finite-rival report, and hash-named projections. Give a model only one file from
`turns/` at a time. `public_archive/` contains all four query inputs for the
controller; it is not a model turn. `private/` and `audit.json` contain answers,
settings, seeds and source identities. Current-turn names depend only on the
visible demos and that query; future query changes cannot change them. The
first turn is identical to the corresponding single-query request.

`audit.py` is reusable by later reviewers and refuses to overwrite existing
outputs. Runtime errors cannot eliminate a rival. A demo-refuted rival needs
no further query replay; surviving rivals are checked on every query.

## Owner handoff

The native inventory is `evidence/manifest.json`. This return contains reviewer
qualification and source-bound execution evidence; owner acceptance and training
admission are separate. After applying the delta, the owner must qualify the
exact integrated source and accept it through the native API. From the repo:

```bash
python3 -m arcpuzzles parametric qualify 5f6fdf4f9900 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/corner-priority-qualification --summary
python3 -m arcpuzzles parametric accept 5f6fdf4f9900 \
  --qualification var/review/corner-priority-qualification/qualification.json \
  --reason 'Reviewed component priority, teaching repair, and causal evidence'
python3 -m arcpuzzles parametric export 5f6fdf4f9900 \
  --count 2 --seed 41 --demos 3 --queries 4 \
  --out var/datasets/corner-priority
```

An inherited canonical test still reports exact-text divergence between catalog
and base authority strings. Its assertions were preserved; bounded Racket parity
matches the labels. The task notes and return report retain that unresolved
finding. This prototype does not silently clear it or other inherited audits.
