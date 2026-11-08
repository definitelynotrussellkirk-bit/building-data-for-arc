# Sort-order staircase: proposed task-local prototype

This directory contains a **proposed, unapproved** parametric extension of task
`b6ba2d176fe8` (`training:03560426`). It does not modify `generator.py`, the
canonical `program_solution`, selected rule authority, source approval, or
training admission.

| Parameter | Allowed values | Default | Effect |
|---|---|---|---|
| `sort_order` | `left_to_right`, `right_to_left` | `left_to_right` | Order source rectangles by horizontal position before drawing the same corner-overlapping staircase. |

Both settings preserve the original reasoning pattern: recover solid colored
rectangles and their dimensions, choose an order, then redraw them from `(0,0)`
with each next top-left at the previous bottom-right. The later rectangle owns
the shared corner. `left_to_right` uses the exact canonical Racket program;
`right_to_left` changes only the unique sort binding by reversing that order.

## Episode interface

The rule setting is fixed once per episode. Demonstration and query counts are
independent:

- demonstrations: `3..8` (default `3`)
- queries: `1..8` (default `4`)

All inputs in an episode are distinct. Sampling is deterministic and bounded; a
request that cannot be satisfied is rejected instead of being padded, cloned, or
silently reduced. The evidence builder runs exact protected Racket for every
label and every declared rival prediction. Rival identification uses only the
demonstrations; query labels are retained privately for verification rather than
used to rescue an ambiguous lesson.

## Run and verify

Run from the outer extraction directory containing `review.py`:

```bash
python3 review.py run python3 \
  generators/b6ba2d176fe8/workspace/parametric/prototype.py emit \
  --all-settings --seed 20261023 --demos 3 --queries 4 \
  --out ../checks/parametric/sort-order-episodes-review-7ab6474ceb76fd4f

python3 review.py run python3 \
  generators/b6ba2d176fe8/workspace/parametric/prototype.py verify \
  ../checks/parametric/sort-order-episodes-review-7ab6474ceb76fd4f \
  --out ../checks/parametric/sort-order-verification-review-7ab6474ceb76fd4f.json

python3 review.py run python3 -m pytest -q \
  generators/b6ba2d176fe8/tests/test_parametric_sort_order.py
```

Output paths are exclusive; use a fresh path for every emission or verification
receipt. Without `--all-settings`, `--sort-order sample` deterministically draws
one hidden setting from the seed and holds it fixed for the whole episode.
Explicit settings bypass that draw.

## Public/private boundary and identity

Only `public/*.json` is model-visible. Each public file contains exactly:

- `train`: demonstration inputs and outputs
- `test`: query inputs only

Its filename is exactly
`sha256(reviewer_support.public_challenge_bytes(visible_challenge)) + ".json"`.
The identifier therefore commits only to the canonical visible bytes; it does
not hash or encode the seed, hidden setting, exact program, query answers, rival
predictions, or source metadata. Those remain under `private/`.

`verify` checks the public inventory, exact canonical bytes and filenames,
redaction, count contract, current source hashes, selected/canonical authority,
saved rule bytes, and fresh protected-Racket reexecution.

## Promotion handoff

`adapter.py` exposes the documented worker boundary:

```python
program(settings) -> str
generate(seed, settings, demos, queries) -> {
    "train": [...],
    "test": [...],
    "program_solution": "...",
}
```

`promotion.json` declares the parameter space, canonical default, and count
limits. The adapter is authoring support for a future independent qualification
worker; its presence is not approval. `generate` returns complete query labels
to that worker, while public export remains the responsibility of the evidence
builder and masks them.

## Limits

The retained evidence is finite. It exercises the two declared settings and
recorded seeds against the one declared alternate, not every lawful grid or every
plausible ARC hypothesis. Inputs are source-bound to the current repaired
production generator. Any later source or contract change must emit fresh
evidence rather than treating these receipts as evergreen.
