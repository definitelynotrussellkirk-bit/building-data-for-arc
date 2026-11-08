# 77871cecd343

Generate a 9–15 row by 9–15 column input with one complete color-9 row/column cross and one 4-connected color-1 source shape in any single quadrant. The selected Racket rule reflects the source across the detected cross in all three other quadrants, painting copies color 8.

Kind: `per_puzzle`. Selected generator version: `2.1.0`. Canonical rule pin: `RULE_HASH = "1bad9bf6a465"`.

Default lessons deliberately vary all four source quadrants and all nine joint cross offsets `(row_offset, col_offset) in {-1,0,1}²`. The 4- and 9-step schedules are coprime, so every quadrant sees every offset pair over 36 consecutive examples; every four-example lesson covers all quadrants and refutes both declared canonical-fitting rivals.

Exact observable controls are `grid_h`, `grid_w`, `row_offset`, `col_offset`, `source_quadrant`, and `shape_cells`. No texture controls are advertised. Approval remains catalog-derived; this repair does not alter approval or the Racket authority.
