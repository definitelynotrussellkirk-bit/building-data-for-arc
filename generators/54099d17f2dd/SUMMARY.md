# 54099d17f2dd

A 0-background grid contains one connected color-2 template and one separate
color-1 marker. Normalize the template to its bounding-box offsets, create a
fresh blank grid of the same dimensions, and stamp those offsets in color 8
with the marker as the new bounding-box top-left. The source template and marker
vanish.

Version `3.0.0` exposes three exact controls only: `grid_h`, `grid_w`, and
`template_shape`. A four-profile constructive schedule includes two leftward,
asymmetric five-cell cases per cycle. Those cases refute two wrong rules that
fit every canonical demonstration: mirror leftward copies, and copy only the
first four template cells.

The selected Racket authority is unchanged and pinned by `RULE_HASH =
"4a6409bfdf9a"`. See `workspace/analyze_shortcuts.py` for a reproducible
canonical-ambiguity/counterexample report and `workspace/reference_probe.py`
for an independent Python oracle plus Racket parity runner.
