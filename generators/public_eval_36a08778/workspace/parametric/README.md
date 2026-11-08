# Falling-ray obstacle routing

Private lesson parameter: `routing_mode=split|closest_exit`. `split` is the exact
public parent. `closest_exit` routes each impact to only the nearer segment end,
with a left tie-break. Inputs are matched across settings. The adapter supports
2–6 demonstrations and 1–4 source queries; training material uses four queries
and shuffles that complete bank before exposing any one-query prefix.

A computes the first horizontal red segment reached by each active downward ray
and its endpoint columns. B consumes those input-dependent bounds to paint the
cap path and choose the next active columns. The protected causal witness replaces
that intermediate with the closest-exit branch and changes the final grid.
