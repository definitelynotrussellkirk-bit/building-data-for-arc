# Proposed panel-count threshold parameter

Status: **proposed task-local prototype**. It does not modify the production
`generator.py`, canonical authority, rule hash, approval state, or training
admission.

## Parameter

`threshold` is fixed once per episode and has exactly three integer values:

| threshold | output cell is 1 when panel count is… |
|---:|---|
| 1 | at least 1 |
| 2 | at least 2 — canonical/default behavior |
| 3 | at least 3 |

The input grammar is unchanged: two complete color-8 row dividers and two
complete color-8 column dividers form nine panels containing color-6 cells.
Only the executed count comparison changes. Every generated demonstration uses
a profile containing counts 0, 1, 2, and 3, so one demonstration separates all
three declared settings; additional demonstrations add input diversity rather
than repair underidentification.

The exact default program in `programs/threshold-2.rkt` is byte-for-byte equal
to the selected canonical `program_solution`. The threshold-1 and threshold-3
files differ only in the comparison constant.

## Runnable evidence command

From the outer packet directory containing `review.py`:

```bash
python3 review.py run python3 generators/a9c4475d7cda/workspace/parametric/prototype.py \
  --seed 17 --threshold all --demos 3 --queries 4 \
  --out ../checks/parametric/a9c4475d7cda-threshold
```

The command chooses no hidden setting when `all` is requested: it builds one
complete episode per threshold over the same deterministic sequence of inputs.
`auto` chooses one setting from the seed once per episode. Demo and query counts
are independent exact integers in 1..16. Sampling is bounded and fails instead
of cloning or silently shortening an episode.

Every retained label and every demonstration-rival fit is re-executed through
the included protected Racket runtime. The output directory's `public/` files
contain only demonstration inputs/outputs and query inputs. Their names are the
full SHA-256 of those visible bytes. Thresholds, seeds, programs, query answers,
and execution records remain under `private/`.

## Promotion adapter

`adapter.py` and `promotion.json` implement the repository's qualification
interface. The adapter returns Python label claims; owner qualification
independently re-executes every label in protected Racket and requires the
chosen threshold to be the sole survivor on demonstrations. Successful local
checks do not accept the family or admit its examples to training.
