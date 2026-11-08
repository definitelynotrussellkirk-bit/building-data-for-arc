# e4cb0224ca42

0-bg grid (h ∈ 7-9, w ∈ 9-11) with: 1-3 SOLID RECTANGLES, each rh × rw where BOTH dimensions are ODD (rh, rw drawn from {3, 5, 7}) — so each rectangle has a well-defined CENTER ROW and CENTER COLUMN. Each rect painted in a DISTINCT non-bg color drawn from {2,3,4,5,6,7,8,9}, placed at a random non-touching position via draw_rect, with a one-cell moat between rectangles. Rule (FOR EACH SOLID ODD×ODD RECTANGLE, PROJECT A CROSS — THE MIDDLE ROW AND MIDDLE COLUMN OF THE BBOX — IN THE RECT'S COLOR, ON A FRESH SAME-SIZE EMPTY GRID): PRODUCE a fresh same-size grid of 0s. For EACH solid rect with both dims odd at bbox (rmin, cmin, rmax, cmax) with color k: COMPUTE middle row mr = (rmin + rmax) // 2 and middle col mc = (cmin + cmax) // 2. PAINT every cell in ROW mr (cols cmin..cmax) and every cell in COL mc (rows rmin..rmax) with color k. Net: each odd×odd rect becomes a color-k cross on a fresh canvas; the rest of each rect's bbox stays 0.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
