# 6ecd6f93877b — Sorted Count Strip

A 5–10 by 5–10 zero-background grid contains 2–5 scattered nonzero colors, each occurring 1–4 times. Count every occurrence of each color, sort colors by numeric value, and emit a one-row strip containing each color repeated by its full count. Positions do not affect the output; an all-zero input would map to `[[0]]` under the pinned rule.

Version `3.0.0` exposes four exact observable controls: `grid_h`, `grid_w`, `n_colors`, and `max_count`. Unknown or invalid controls fail loudly. The default curriculum alternates canonical-density anchors with broad cases containing a count of four and an output longer than six, refuting the two strongest shortcuts that fit all five labeled pairs. Three demonstrations are required, and every four-pair query rotation retains a declared shortcut witness.

Rule hash: `66d1273fdbac`. The Racket authority is unchanged. Approval is derived by the catalog from current code and retained evidence; reviewer checks do not grant training admission.
