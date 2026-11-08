# 964b23808a3c

For each column whose **last nonzero marker is color 5**, read its nonzero
markers from top to bottom. Fill row 0 through the first marker with that
marker's color, then fill each subsequent interval through the next marker with
the **current/lower marker's color**. Leave every non-target column unchanged;
when the terminal 5 is above the bottom edge, also leave the rows below it
unchanged.

The default four-example schedule cycles through exact canonical
shape/palette profiles `7×7×3`, `12×12×7`, `13×13×9`, and `17×17×10`.
The latter two profiles add lawful distractor columns, including a multi-marker
non-target column and a column that contains 5 internally but ends in another
color. The schedule supplies three demonstrations and one query; every four-pair
window remains identifiable under each query rotation against six declared
plausible rivals.

Exact controls: `grid_h`, `grid_w`, `n_targets`,
`n_marks_per_target`, `distractor_mode`, and `terminator_position`.
Unknown, mistyped, or out-of-range overrides are rejected rather than clamped.

Kind: `per_puzzle`. Reviewed version: `3.0.1`.
Canonical rule hash: `c7e69da25375`.
Approval remains derived by the catalog from current code and retained evidence.
