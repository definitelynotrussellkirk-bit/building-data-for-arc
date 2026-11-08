# a44e3443619f

0-background grid (h≈7–9, w≈9–11) with exactly two or three isolated red X patterns. Each pattern has color-2 cells at the four diagonal corners of a 3×3 region; its centre and edge cells are 0. The constructive sampler rejects any layout whose combined corners would create an unintended extra centre. Rule: for every cell `(r,c)`, if the input value is 0 and all four immediate diagonal neighbours (with out-of-bounds default 0) are 2, change it to blue 1; otherwise preserve it.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence. The task-local parametric workspace proposes an unapproved `single|cascade` family; owner qualification and acceptance remain separate.
