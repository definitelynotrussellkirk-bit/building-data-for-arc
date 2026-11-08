# Exposed solve notes

I inspected only `solve/challenge.json` after preparation. I had earlier exposure to the task rule while repairing its generator, so this is explicitly not a blind solve.

Hypothesis from the three visible pairs: color 9 is a control marker. Treat every nonzero/non-9 monochrome 4-connected component as an object, measure the minimum Manhattan distance from any object cell to the marker, select the nearest object, and return its tight crop. The second training example distinguishes nearest-cell distance from just selecting the visually smallest/closest-looking compact object. I use top row then left column as deterministic tie-breaks because the visible examples do not contradict it and a total order is needed.

Predicted test outputs before checking:

1. The vertical color-2 domino immediately below the marker, `[[2], [2]]`.
2. The color-3 L triomino above the marker, `[[3, 3], [3, 0]]`.
