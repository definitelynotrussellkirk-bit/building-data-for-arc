# Ladder threshold and bar alignment — proposed parametric prototype

This task-local prototype is separate from the selected canonical generator and
its approval. It does not change the catalog, canonical Racket authority,
shared runtime, or training admission. The original/default setting is
`min_rung_width=3, bar_alignment="left"`; `materialize_rule(3, "left")`
returns the exact canonical program text and the evidence command executes it on
every retained canonical pair.

## Parameters

| Parameter | Allowed values | Default | Executed effect |
| --- | --- | --- | --- |
| `min_rung_width` | `3`, `4`, `5` | `3` | A row counts as a rung only when its floor color occupies at least this many contiguous cells. |
| `bar_alignment` | `left`, `right` | `left` | The three-cell output bar is filled from the left or right; separator and gray-minimum logic are unchanged. |

The floor roles, floor-color identity, contiguous-run test, rung counting,
maroon separator, smallest-positive selection, and later-index tie break remain
invariant. Settings are selected once from the episode seed before input draws
and remain fixed across all demonstrations and queries. Changing `n_train` or
`n_test` does not resample the setting.

Every authored scene contains three floor bands with candidate run lengths that
produce count vectors `(3,2,2)`, `(2,2,2)`, and `(1,1,2)` under thresholds 3,
4, and 5. Incomplete two-cell distractor rows do not count. Therefore each
single demonstration separates all six threshold/alignment combinations; the
retained check nevertheless evaluates all demonstrations using only their
visible labels. Query answers are never used for identifiability.

## Exact commands

Run from the outer extraction directory containing `review.py`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/7b088f161470/tests/test_generator_7b088f161470.py \
  generators/7b088f161470/tests/test_shortcut_repair.py \
  generators/7b088f161470/tests/test_parametric_7b088f161470.py

python3 review.py run python3 \
  generators/7b088f161470/workspace/parametric/prototype.py \
  --all-settings --seed 7319 --n-train 3 --n-test 4 \
  --out ../checks/parametric-7b088f161470-v2
```

One explicit episode:

```bash
python3 review.py run python3 \
  generators/7b088f161470/workspace/parametric/prototype.py \
  --seed 44 --min-rung-width 5 --bar-alignment right \
  --n-train 3 --n-test 4 \
  --out ../checks/parametric-7b088f161470-single
```

`n_train` and `n_test` are independent exact integers in `1..128`; the writer
rejects invalid values and duplicate visible payloads rather than truncating.

## Evidence and visibility

The all-settings command writes:

- `public/challenge-<sha256>.json`: visible demonstrations and unlabeled query
  inputs only. The identifier is the SHA-256 of exactly those visible bytes.
- `private/episode-NNN.json`: seed, selected parameters, query outputs, exact
  rule text/hash, input/output hashes, and demonstration-only survivors.
- `private/rules/<sha256>.rkt`: the exact Racket program executed.
- `report.json`: canonical parity, episode paths/settings, source identities,
  commands, and bounded limitations.

Public filenames and IDs are derived only from the exact visible challenge bytes;
private seed/parameter fields, Racket text, query answers, and private ordinals are
not mixed into that hash. Private episode filenames are numeric. The batch is
sorted by public ID. Rule artifacts are written byte-exactly under their SHA-256
and a pre-existing mismatched artifact is rejected.

The tests include six hand-derived Racket outputs, Python/Racket parity,
canonical default execution, all-setting demonstration identifiability, four
distinct queries, reproducibility, setting stability under count changes,
argument rejection, and public/private separation. These are bounded proposed
variants, not proof of unrestricted ARC uniqueness or production approval.
