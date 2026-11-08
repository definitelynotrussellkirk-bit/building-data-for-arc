# d833a288bd7d parametric source-cue family

This task-local adapter preserves the approved canonical rule exactly under the
`yellow_marker` default and adds one nearby alternative, `minority_centroid`.
The input distribution is shared between settings; only the episode-fixed rule
changes.

## Rule settings

- `yellow_marker` (default): derive the source diagonal from the isolated yellow
  cell on one expanded corner of the dense square. `canonical.rkt` is byte-for-
  byte identical to the canonical catalog program (SHA-256
  `4f1476e0a09bb89804dc679485b5b6c8e14562ea16130d6a4f2b9091cd9dea5d`).
- `minority_centroid`: identify the strict minority of colors 1 and 8 inside the
  dense square, compute its centroid quadrant, and use that as the source
  diagonal.

Both settings then locate the yellow L-cluster target diagonal, compute
`(target_diag - source_diag) mod 4`, rotate the dense square by that many quarter
turns, and move the yellow marker to the target expanded corner. Thus Step B
cannot choose the final rotation before Step A supplies the input-dependent
source diagonal.

## Episode contract

`adapter.py` exposes the native promotion API declared by `promotion.json`.
Supported counts are 2–6 demonstrations and 1–4 queries; native qualification
uses three demonstrations and four queries. Generation is deterministic and
prefix-stable by `(seed, split, index)`, and the visible inputs are identical
across settings. Query 4 is a substantive 30×30 case with a dense 16×16 colored
square (256 shape cells plus four yellow cells).

The first two demonstrations distinguish both declared settings and the finite
named rivals implemented by `teaching_certificate`: reverse direction,
majority centroid, all fixed turns, and all fixed source diagonals. This is a
bounded curriculum check, not a uniqueness proof.

## Reproduce the retained checks

From the packet's outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/d833a288bd7d/tests/test_parametric_source_cue.py -q
python3 WORK/check_public_exports.py \
  WORK/repo/generators/d833a288bd7d/workspace/parametric/evidence/current/public \
  --demos 2 --queries 4
python3 review.py run python3 -m arcpuzzles parametric qualify d833a288bd7d \
  --out ../checks/d833a288bd7d/qualification --summary
```

The native source inventory is `evidence/manifest.json`. Qualification and
protected-Racket execution receipts are under
`WORK/checks/d833a288bd7d/qualification/`; the wrong-intermediate causal witness
and independent replay are under `WORK/checks/d833a288bd7d/causal/`.

## Limits

The adapter is reviewer-reported `ready`, not owner-accepted. The retained
finite rival audit, fresh seeds, and protected-Racket labels do not establish
universal identifiability or measured training gain, and no artifact here admits
training data.
