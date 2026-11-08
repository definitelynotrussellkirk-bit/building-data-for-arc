# Rank-delta parametric prototype

This task-local prototype leaves the selected canonical generator and canonical
Racket authority unchanged. It varies one hidden episode-wide rule parameter:

- `rank_delta = 0` (**canonical/default**): fill a zero cell with its row label
  when the row and column labels are the same color/rank.
- `rank_delta = 1` (**proposed**): fill with the row label when that label is the
  next color run after the column label in the borders' shared ordered palette.

The invariant reasoning is unchanged: read the right-border row label and
bottom-border column label, recover the borders' shared ordered colors, compare
the two labels, preserve every nonzero border cell, and paint from the row label.
The parameter changes the executed comparison relation rather than grid size,
placement, color identity, or sampling weights. It is fixed across all
representations and queries in an episode.

The prototype produces two episodes (one per setting), two demonstrations and
four distinct queries per episode, obtains every label from the exact matching
Racket program, checks an independent Python mirror, and tests the other setting
as a declared rival using demonstrations alone. Public challenge filenames are
SHA-256 IDs of exactly the visible demonstration pairs and query inputs; private
settings, seeds, programs, and query outputs do not affect them.

## Exact replay

From the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/dafb4f819b93/workspace/parametric/prototype.py materialize \
  --out-dir ../checks/parametric/dafb4f819b93-rank-delta \
  --seed 31 --train 2 --test 4

python3 review.py run python3 \
  generators/dafb4f819b93/workspace/parametric/prototype.py verify \
  --out-dir ../checks/parametric/dafb4f819b93-rank-delta
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/dafb4f819b93/tests/test_generator_dafb4f819b93.py \
  generators/dafb4f819b93/tests/test_parametric_rank_delta.py
```

The retained evidence is bounded to the declared values, generated episodes,
and one competing setting per episode. This is a **proposed prototype**, not a
production parametric API, canonical-rule change, approval, or training admission.

## Additional cyclic label-offset proposal

[label_offset.py](label_offset.py) ports `review-15adbf6fd2d4a85d` beside
the current rank-delta prototype. Its alternate selects the next column label
in cyclic border order, including wraparound. The current `rank_delta=1` instead
compares row-rank minus column-rank without wraparound. These are distinct
proposed relations; the canonical/default source is identical in both.

```bash
python3 review.py run python3 generators/dafb4f819b93/workspace/parametric/label_offset.py \
  --seeds 1 0 --n-train 3 --n-test 4 --out ../checks/parametric/label-offset
python3 review.py run python3 generators/dafb4f819b93/workspace/parametric/label_offset.py \
  --verify-only --out ../checks/parametric/label-offset
```

Current owner reconciliation retains the prior reviewer-reported rank-delta
receipts as prior-source evidence and separately records focused checks against
the generator's added semantic contract. Neither variant is approved or
training-admitted.
