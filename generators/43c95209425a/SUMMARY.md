# 43c95209425a

0-bg grid (h~8-12, w~9-14) with: (a) ONE GREEN(3) SEED at (start_r, 1) on the LEFT EDGE INTERIOR (start_r ∈ [2, h-3]); (b) 0-2 STEERING DOTS placed at fixed positions in column w-3 — first DOT in COLOR 8 at (r, w-3), second DOT in COLOR 4 at (r-1, w-3), third DOT in COLOR 6 at (r+1, w-3) (turn_dots controls how many of these appear). Rule (GREEN SEED WALKS RIGHTWARD, TURNING AT STEERING DOTS, PAINT PATH GREEN): the green seed at (start_r, 1) marches RIGHTWARD across empty cells, painting each traversed cell COLOR 3. When the path reaches a STEERING DOT cell, the dot's color encodes a TURN: COLOR 8 = turn left or continue, COLOR 4 = turn up, COLOR 6 = turn down (per puzzle convention). Continue until grid edge. Net: a green trail snakes from the left seed via steering dots toward the right side.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
