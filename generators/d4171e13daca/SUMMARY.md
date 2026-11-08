# d4171e13daca

A zero-background grid contains 2-5 disjoint hollow blue rectangular frames,
each strictly inside the previous frame with at least one blank cell of
separation. Recolor the outermost frame 2, the next frame 3, then 4, 5, and 6
moving inward, leaving every other cell 0.

Version: `3.1.0`. Kind: `per_puzzle`. `EXAMPLES_NEEDED = 4`.
Four demonstrations plus one query are drawn from a five-profile cycle. Every
single-pair query holdout retains shallow/deep support plus inset, non-square,
and off-center witnesses against the declared canvas-distance and recentering
shortcuts. Exact controls remain `frame_count=2..5`,
`layout_style=canonical|offset`, and `outer_margin=edge|inset`.

The canonical Racket authority is unchanged at `RULE_HASH = 17513141906a`.
See `notes.md`, `tests/`, and `workspace/query_rotation_probe.py` for the repair,
retained failures, and replayable finite curriculum evidence.
Approval is derived by the catalog from current code and retained evidence.
