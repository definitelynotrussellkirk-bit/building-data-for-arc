# Marker-slice relay parametric prototype

The default `checkerboard_only` setting returns the exact canonical Racket
program. `marker_slice_relay` first completes that checkerboard, then copies the
completed row or column selected by each external color-8 marker into an equal
exterior lane. Inputs are shared between settings; demonstrations and queries
are independently selectable in the ranges 2–6 and 1–4.

Focused check:

```sh
python3 review.py run python3 -m pytest generators/78cc0b96bc87/tests/test_parametric_marker_slice_relay.py -q
```
