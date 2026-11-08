# Proposed proximity-radius prototype

This directory is **not** part of the selected production path. The catalog and
canonical Racket rule remain unchanged. The prototype varies one hidden setting
once per complete episode:

| Parameter | Allowed values | Original/default |
|---|---|---|
| `proximity_radius` | exact integers `0`, `1`, `2` | `1` |

Paired blue edge markers still define complete rows/columns. Every output draws
those lines blue. A red rectangle is recolored blue when its minimum
perpendicular distance from any marked row/column is at most the episode's
radius. Thus radius `0` requires intersection, radius `1` is the exact canonical
"intersect or one cell away" rule, and radius `2` adds the next distance band.

Every retained input contains witnesses at distances `0`, `1`, `2`, and `4`, so
each demonstration distinguishes all three settings while a far red object
still witnesses selective recoloring. The prototype exposes demonstration and
query counts separately; retained evidence uses three demonstrations and four
distinct queries.

Generate one private episode from the packet extraction root:

```bash
python3 review.py run python3 \
  generators/19c5f15066d3/workspace/parametric/prototype.py \
  --seed 1 --proximity-radius 1 --n-train 3 --n-test 4
```

Materialize and exact-Racket-verify one retained episode per setting, including
all four queries and both rival settings, with this exact command:

```bash
python3 review.py run python3 \
  generators/19c5f15066d3/workspace/parametric/verify.py \
  --out-dir ../checks/parametric/19c5f15066d3-proximity-radius-v1
```

The verifier also checks radius `1` against all four canonical pairs, stores
private rules/answers separately from public challenges, and derives each
public filename solely from visible demonstration pairs and query inputs. Batch
artifacts are sorted by that visible ID, and duplicate visible payload IDs are
rejected before any episode files are emitted. This is bounded proposed evidence
only: it neither changes nor approves the selected canonical generator, variants,
or training data.
