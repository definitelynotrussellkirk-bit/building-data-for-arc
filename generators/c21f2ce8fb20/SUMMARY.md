# c21f2ce8fb20

Gray walls (5) bound three or four separated rectangular chambers whose interiors contain blank cells (0) and red seeds (2). Count red seeds in every chamber. Select the unique chamber with the greatest seed count, then emit a same-size all-zero grid with every cell of that chamber painted cyan (8), including its former seed cells.

The v3 curriculum alternates four deterministic profiles: canonical-shaped three-room scenes, canonical-shaped four-room scenes, a four/five-seed winner against a three-seed decoy, and a size/density decoy where the true winner is neither the largest nor the densest room. Public exact controls are `grid_h=8..16`, `grid_w=11..20`, `n_chambers=3..4`, and `winner_seeds=2..5`; all advertised combinations are generated, observed, and validated.

Named rivals are `prefer_exactly_three`, `largest_room`, and `densest_room`. Every four-example cyclic lesson window refutes all three, while `prefer_exactly_three` is retained as the strongest canonical-fit shortcut because it matches all five canonical demonstrations.

Kind: `per_puzzle`. Generator version: `3.0.0`. Canonical rule hash: `b86be3a37a68`.
Approval remains catalog-derived from current code and retained evidence.
