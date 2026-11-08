# 0ee277d96857

Square n × n input grid (n ∈ {2..5}) with: (a) g[0][0] = LINE COLOR (a non-0 value drawn from {1..9}); (b) other cells filled by one of 5 DECORATIONS (solid / noise_with_corner / stripes_with_corner / checker_with_corner / blob_with_corner) using a SECOND color (line_color + 1, wrapping). The decoration is decoy — only g[0][0] matters. n encodes the period and line_color encodes the output stripe color. Rule (PRODUCE A FIXED 15×15 PERIODIC LATTICE WITH PERIOD n+1 AND LINE COLOR g[0][0]): EXTRACT line_color = g[0][0] and period = n+1 (where n is the input's side length). PRODUCE a FRESH 15 × 15 OUTPUT GRID. For EACH cell (r, c) with r, c ∈ [0, 14]: IF (r % period == n) OR (c % period == n), PAINT it with line_color; ELSE bg-0. The input's decoration content is DROPPED. Net: a fixed 15×15 grid with horizontal and vertical lines spaced every (n+1) cells in the line color — a lattice pattern. Flagged intrinsic-low (uniq_out=31): bounded by 4 period values × 9 colors.

Kind: `per_puzzle`. Imported version: `2.1.5`.
Approval is derived by the catalog from current code and retained evidence.
