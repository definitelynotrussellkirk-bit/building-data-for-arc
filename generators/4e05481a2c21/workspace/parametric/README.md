# Hole-area pack ordering

This native opt-in family keeps the source task's complete enclosed-hole
extraction and horizontal packing operation while varying one private,
episode-fixed parameter:

| `pack_order` | Rule |
|---|---|
| `left_to_right` | Exact selected canonical Racket program, byte-for-byte. |
| `hole_area_descending` | Extract every object's complete enclosed-zero union, count its cells, then pack the extracted patterns by descending derived area; ties remain left-to-right. |

The input sampler is independent of the setting. It supports 2–6 demonstrations
and 1–4 queries independently. The first two demonstrations distinguish both
settings and ten declared ordering shortcuts. Additional demonstrations are
prefix-stable. Every four-query episode ends with a 30×30 scene containing four
large boundary-spanning objects and at least 120 foreground cells.

## Sequential dependency

**A:** segment each colored object and extract its complete four-connected
enclosed-zero union. **Intermediate:** the per-object vector of exact enclosed
cell areas. **B:** use that vector to choose the descending-area pack order and
then place the already-extracted patterns. B cannot be selected from object
position, object size, hole bounding boxes, colors, or region counts before A's
result exists.

`bbox_area_descending.rkt` is a private counterfactual, not an admitted setting.
It keeps extraction and packing but substitutes each extracted union's bounding-
box area for its cell area. The retained protected-Racket witness changes the
pack order and 14 final cells.

## Public projection

`prototype.public_view(episode, query_index)` returns demonstrations plus only
the current query input. It excludes the private setting, seed, programs, all
query answers, and future query inputs. Query 0 is byte-identical whether the
controller requested one query or all four. Public IDs are SHA-256 hashes of
`reviewer_support.public_challenge_bytes` only.

## Reproduce

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest \
  generators/4e05481a2c21/tests/test_parametric_family.py -q

python3 review.py run python3 \
  generators/4e05481a2c21/workspace/parametric/self_audit.py \
  --out generators/4e05481a2c21/workspace/parametric/evidence/new-run \
  --seeds 0,17

python3 review.py run python3 -m arcpuzzles parametric manifest 4e05481a2c21 \
  --evidence generators/4e05481a2c21/workspace/parametric/evidence/current \
  --include generators/4e05481a2c21/tests/test_parametric_family.py \
  --reported-checks 'State only the exact checks actually rerun'

python3 review.py run python3 -m arcpuzzles parametric qualify 4e05481a2c21 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/4e05481a2c21/qualification --summary
```

Qualification and the task-local audit establish correctness only for their
bounded settings, seeds, counts, and finite rivals. They do not prove universal
identifiability, measured learning value, owner acceptance, or training
admission.
