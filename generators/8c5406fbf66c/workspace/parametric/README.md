# 8c5406fbf66c parametric window relay

`window_scope=all` is the exact selected canonical program: mark the top-left
cell of every nonzero same-color 2×2 window.

`window_scope=key_count_relay` adds a real dependency. Step A counts the active
2×2 windows in the unique color-1 source rectangle. That count (1, 2, or 3) is
the intermediate. Step B sorts the three candidate objects by occupied area,
selects the candidate at that rank, and applies the canonical 2×2 top-left
marking only to that selected object. Candidate colors, placements, areas,
aspect ratios, and source orientation vary; color 9 supplies isolated distractors.

The input stream is matched across settings. Demonstrations and queries are
prefix-stable for independent 2–6 / 1–4 requests, and the fourth query is a
substantive 30×30 boundary case. `wrong_rank_one.rkt` is an audit-only
wrong-intermediate counterfactual, not an admitted setting.
