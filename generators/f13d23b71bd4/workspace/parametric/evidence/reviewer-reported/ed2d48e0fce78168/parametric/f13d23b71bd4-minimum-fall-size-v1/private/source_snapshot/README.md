# Proposed `minimum_fall_size` prototype

This directory is **not** part of the selected production path. The canonical
rule and approved/default setting remain unchanged: monochrome 4-connected
objects of size **4 or more** fall straight down to the canvas bottom.

The prototype adds one bounded hidden parameter selected once per complete
episode:

| Parameter | Allowed values | Canonical/default |
|---|---:|---:|
| `minimum_fall_size` | `3`, `4`, `5` | `4` |

Every authored input comes from the selected generator's existing
`mixed_sizes_1_to_6` profile. It contains one object of each size 1 through 6,
so sizes 3 and 4 distinguish all three settings while preserving the original
object extraction, fresh-canvas repainting, downward translation, and collision
order. Demonstration and query counts are independent; the retained command
uses three demonstrations and four distinct queries per episode.

Run the focused tests from the packet extraction root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/f13d23b71bd4/tests/test_parametric_minimum_fall_size.py
```

Materialize and Racket-verify one complete episode for each setting:

```bash
python3 review.py run python3 \
  generators/f13d23b71bd4/workspace/parametric/prototype.py \
  --seeds 0 1 2 \
  --demo-count 3 \
  --query-count 4 \
  --difficulty medium \
  --out ../checks/parametric/f13d23b71bd4-minimum-fall-size-v1
```

The command writes exact private Racket programs and answers, source snapshots,
canonical-default checks, rival-threshold checks, and answer-masked public
challenges. Public filenames are SHA-256 identifiers derived only from visible
demonstrations and query inputs; private settings and query answers cannot alter
them. Batch episode metadata and retained public files are ordered by that public
ID, independent of caller seed order.

The retained evidence is finite and source-bound. It proposes a coherent
teaching extension only; it does not approve a production variant or admit any
trajectory to training.
