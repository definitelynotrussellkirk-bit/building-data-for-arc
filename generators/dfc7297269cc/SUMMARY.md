# dfc7297269cc — Horizontal sandwich fill

Fill a zero exactly between equal nonzero **horizontal** neighbors, using the original grid simultaneously. All other cells stay unchanged.

Selected generator version: `2.0.0`. Selected rule hash: `80ec61287499`.

The generator exposes four exact controls (`grid_h`, `grid_w`, `motifs`, `n_colors`) and embeds a transformed 5x7 teaching tile. Every ordinary draw contains 1–4 positive sandwiches plus three negative witnesses: a two-zero same-color span, unequal one-zero endpoints, and a vertical sandwich. These refute the canonical-fitting `span_fill`, `any_nonzero_endpoints`, and `horizontal_or_vertical` shortcuts.

Task-local regressions and reusable independent probes are under `tests/` and `workspace/reference_probe.py`.


## Parametric sidecar

A reviewer-ready native sidecar keeps `horizontal_all` as the exact canonical default and adds `ranked_vertical`: the number of canonical horizontal sandwiches selects the same-ranked vertical sandwich to complete. It supports 2–6 demonstrations and 1–4 prefix-stable queries; production `generator.py` and canonical authority are unchanged. See `workspace/parametric/`.
