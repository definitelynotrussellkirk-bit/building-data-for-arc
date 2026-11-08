# Straight-block-position prototype (proposed, not canonical)

This task-local prototype preserves the original objects and reasoning skeleton:
one red source, one blue destination, a shortest Chebyshev path, green interior
cells, and one contiguous block containing every dominant-axis step. It varies
one small rule parameter once per episode:

| Parameter | Values | Canonical/default |
| --- | --- | --- |
| `straight_block_position` | `after_first_diagonal`, `before_diagonals` | `after_first_diagonal` |

The canonical setting takes one diagonal step, then all straight steps, then the
remaining diagonals. The proposed setting takes all straight steps first and
then all diagonals. The input distribution stays within the selected generator's
ordinary unequal-gap grammar, so the two settings produce visibly different
paths. Four labelled demonstrations identify the episode setting before the
held-out query.

The script materializes the exact canonical Racket program and an alternative
that replaces only the phase-order `cond`. It executes both programs through the
included Racket bridge, checks each result against a task-local Python mirror,
and writes public/private evidence separately. Public files omit the hidden
parameter, Racket source, and query answer.

From the packet extraction directory, run:

```bash
python3 review.py run python3 generators/f6b9f647b109/workspace/parametric/prototype.py \
  --difficulty easy \
  --out-dir ../checks/parametric/straight-block-position
```

When `--seeds` is omitted, the tool deterministically chooses the first two
non-negative seeds that cover both settings. The retained summary records those
seeds, selected schedule starts, source hashes, Racket hashes, differing
demonstrations, and query disagreement.

This is bounded **proposed prototype** evidence. It does not modify the selected
canonical generator, `RULE_HASH`, production rule, approval state, or runtime API.
The two settings are not claimed to exhaust every meaningful path-order variant.
