# Visible-only solve notes

Earlier rule exposure exists from the generator review, so this is not a blind solve. During this solve episode I used only `solve/challenge.json` and did not reopen the generator, Racket source, reference solutions, private labels, or the preserved prior solve.

Visible examples show one red cell (2) beside one blue cell (1). The red-to-blue displacement is the initial beam direction. The beam crosses the blue marker unchanged, paints traversed zero cells with 8, and stops before gray (5) or at the grid edge.

The mirror behavior is determined directly from the examples:
- With direction right, 6 turns down; with direction down, 6 turns right. This is `(dr, dc) -> (dc, dr)`.
- With direction down, 4 turns left; with direction left, 4 turns down. This is `(dr, dc) -> (-dc, -dr)`.

I therefore implemented a stateful simulator. It reads obstacle colors from the original input while writing 8s to a copy, and tracks `(row, col, dr, dc)` states to terminate safely if a mirror layout loops. This is my first and only solution revision for the final source hash.
