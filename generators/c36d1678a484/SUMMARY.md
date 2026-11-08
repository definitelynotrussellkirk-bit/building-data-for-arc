# c36d1678a484

A 0-background grid contains one or two **target rows** whose only nonzero cell is orange (`7`). The reference rule treats rows independently: a row is filled entirely with orange exactly when its nonzero sequence is `[7]`; every other row is unchanged.

Version `3.0.0` deliberately places three nearby negative examples in every ordinary draw: a partial row with multiple orange cells, a singleton non-orange row, and a mixed row with exactly one orange cell plus another color. These refute the tempting shortcuts “fill any row containing 7,” “expand any singleton,” and “fill any row with exactly one 7 regardless of other colors.”

Exact override axes are `grid_h=5..12`, `grid_w=3..14`, `target_rows=1..2`, and `palette_kind=mono|warm|cool|contrast`; all combinations are constructive. Core sampling favors the canonical `6x7` three-color profile while broad sampling retains the full advertised domains in every difficulty band. The Racket authority is unchanged.

Kind: `per_puzzle`. Selected version: `3.0.0` (repair of imported `2.0.1`).
Approval is derived by the catalog from current code and retained evidence.
