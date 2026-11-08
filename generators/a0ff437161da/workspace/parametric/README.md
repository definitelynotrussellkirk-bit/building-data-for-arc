# Proposed tie-order episode prototype

This isolated tool keeps the selected generator and canonical task fixed while
varying one hidden episode-level parameter: priority among equally near
corners. The canonical/default setting is `ul_ur_ll_lr`; the bounded rival is
`lr_ll_ur_ul`. Each episode uses one setting for all three demonstrations and
the query. The four retained fixtures are top, bottom, left, and right ties, so
every demonstration separates the two declared settings.

Run from the packet root:

```bash
python3 review.py run python3 \
  generators/a0ff437161da/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --out ../checks/parametric/tie-order
```

Focused regression tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/a0ff437161da/tests/test_parametric_tie_order.py
```

The output deliberately separates public challenges from private rules,
parameters, and query answers. It is marked `proposed_unapproved`; it is an
executable research aid rather than a production interface change.
