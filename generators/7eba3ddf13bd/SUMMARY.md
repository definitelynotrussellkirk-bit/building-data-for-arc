# 7eba3ddf13bd — shortest paths with exact-count portals

Version **3.0.1**. Inputs only; selected canonical Racket rule unchanged (`f97ce42855bc`).

Sparse walled mazes with start 2, goal 3, and automatic portal pairs: any color 4–9 occurring exactly twice. A four-example sliding schedule covers a required single pair, a two-pair chain, a better non-portal route, and three-occurrence non-portal decoys. Ordinary draws have a unique shortest route and paint at least one zero cell 8.

Declared overrides are only `grid_h=7..14`, `grid_w=9..18`, and `portal_color=4..9`; all are legal in every difficulty band. Default geometry is canonical-scale weighted. Unknown keys and negative fixture textures are rejected.

`EXAMPLES_NEEDED=4`. Semantic validation targets four explicit canonical-compatible rivals; it does not assert exhaustive shortcut elimination. Keep consecutive sample indices or revalidate lessons after resampling.

Review evidence: full battery 12/12 green; task-local tests 49 passing; public suite 132 passing; independent probe 610/610 Racket agreements including 600 distinct non-identity, unique-shortest-route generated cases. This is input/label validation, not measured downstream model accuracy.

Probe and boundary fixtures: `workspace/portal_probe.py`, `workspace/portal_cases.json`. Design details: `notes.md`. Approval remains derived from current source and retained evidence; this review does not edit approval records.
