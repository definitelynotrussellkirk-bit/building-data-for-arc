# fdd447a064fe

0-bg grid (h~10-18, w~10-16) with 3-5 RECTANGULAR BARS anchored at a SHARED BASELINE (a varied row, not always the bottom). Each bar has: (a) WIDTH (1-4 cells, from width_dist uniform_1/uniform_2/all_2/mixed/wide); (b) HEIGHT from height_dist (ascending/tight_spread/wide_spread/shuffled), with 2*h_b ≤ grid_h. Bars don't overlap horizontally; spacing 0-2 cells between them. Each bar uses a DISTINCT color from 1..9. Rule (JUMP EACH BAR UP BY OWN HEIGHT): for EACH BAR with height h_b at columns c0..c0+w_b-1 TRANSLATE the bar UPWARD by h_b cells — paint the bar's cells at the new top position one bar-height above its current baseline. Net: each bar doubles its vertical extent by jumping up its own height.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
