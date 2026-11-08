# 15dd333aa99b

0-bg grid (h, w~8-13) with 2-4 PAIRS of equal-colored ENDPOINT MARKERS in DISTINCT colors from {1..9}. EACH PAIR is aligned EITHER HORIZONTALLY (same row, ≥2-cell gap between endpoints) OR VERTICALLY (same col, ≥2-cell gap) — orientation chosen once per task. Each pair occupies a distinct row (or column). No other cells. Rule (BRIDGE ENDPOINT PAIRS INTO FULL SEGMENTS): For EACH PAIR of same-color cells at (r, c1) and (r, c2) with c1 < c2 (horizontal), PAINT all cells (r, c1)..(r, c2) with that color (fill the gap). For VERTICAL pairs at (r1, c) and (r2, c), PAINT (r1..r2, c). Endpoints stay. Net: each endpoint pair turns into a full colored line segment.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
