# 28f91ad53b1b

Wall-aware Voronoi fill from 2–5 distinct one-cell color seeds. Color 5 is an impassable wall; every nonwall cell takes the reachable seed color with minimum four-neighbor BFS distance; finite ties choose the smaller color; seedless components remain 0.

The selected `3.1.0` generator uses a canonical-style zero border and inset gray frame with five recoverable semantic profiles: open Voronoi, wall detour, tie order, seedless rooms, and mixed rooms. Five consecutive demonstrations cover all profiles, and a six-pair lesson remains distinguishable under any one query rotation against the declared plausible rivals.

Exact controls: `grid_h=8..10`, `grid_w=10..12`, `n_seeds=2..5`, and `texture=open_voronoi|wall_detour|tie_order|seedless_rooms|mixed_rooms`. Rule hash: `443a7da44ab8`.
