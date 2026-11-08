# Parametric ray-deflection prototype

This directory contains a **proposed research prototype** for generator
`8eb9146172f8`. It does not replace the production generator or the canonical
Racket authority.

## Episode parameter

| Parameter | Declared values | Canonical default | Episode semantics |
|---|---:|---:|---|
| `deflection_distance` | `1`, `2` | `1` | After each red trigger, every cyan ray shifts away from the red edge by this many cells before continuing inward. |

The setting is fixed for an entire episode. Demonstrations and queries share
that setting, while the visible public challenge contains only demonstration
inputs/outputs and query inputs. Query outputs, the parameter value, rival
predictions, seeds, and rule text remain private.

Distance `1` materializes the exact canonical Racket source. Distance `2`
changes only the four signed shift constants (`+1/-1` to `+2/-2`); ray origin,
travel direction, red-trigger order, clipping, palette, and input grammar are
unchanged. Labels are produced by executing the materialized Racket program
through the bundled real runtime rather than by a Python labeler.

## Why this is a meaningful variant

The public evaluation task `20a9e565` is used only as inspiration for varying
and inferring a repeated spatial stride. The transferred idea is: examples can
identify a fixed displacement magnitude and queries require extrapolating that
same magnitude. This prototype makes no lineage, equivalence, or measured
relative-difficulty claim about that task.

Each retained episode uses independently configurable demonstration and query
counts. The default evidence build has three demonstrations and four distinct
queries. Every retained input separates the two declared settings; all
training examples therefore identify the episode setting, and every query
also has a rival-setting counterfactual.

## Run

From the review bundle root:

```bash
python3 review.py setup
python3 review.py run python3 -m pytest -q \
  generators/8eb9146172f8/tests/test_parametric_deflection_distance.py

python3 review.py run python3 \
  generators/8eb9146172f8/workspace/parametric/prototype.py \
  --seed 20261023 \
  --all-settings \
  --demos 3 \
  --queries 4 \
  --start 0 \
  --difficulty medium \
  --out ../checks/parametric/deflection-distance-s20261023-v1
```

The output directory contains:

- `manifest.json`: source/runtime hashes, canonical parity, episode summaries,
  public IDs, and stated limits.
- `private/`: full episodes, exact Racket programs, canonical-parity records,
  same-input counterfactual evidence, hidden settings, and query answers.
- `public/`: byte-canonical ARC challenges named solely by a hash of their
  visible contents.

The writer refuses to overwrite an existing evidence directory. Use a new
versioned directory for a new run.

## Evidence contract and limits

The focused tests pin exact canonical-text parity at distance `1`, a
hand-derived distance-two staircase, malformed-setting rejection, fixed
episode semantics, distinct queries, rival identifiability, and public/private
separation. The evidence writer additionally replays all labeled canonical
pairs and records a same-input counterfactual for both settings.

The declared parameter set is deliberately finite (`{1, 2}`). Evidence covers
the retained seeds and role templates, not every possible seed, and does not
claim that these are the only coherent variants of the source puzzle.
