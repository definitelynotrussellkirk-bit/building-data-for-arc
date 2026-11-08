# Native room-match neighbor relay

`match_only` is the exact canonical room-signature matcher. `mark_match_neighbors`
uses the canonical one-hot match strip as an intermediate: it recovers the
selected room and marks candidate positions connected to that room by color-7
doorways with color 4, preserving the selected position as 8.

The deterministic bounded sampler guarantees that the first same-area room is
a different candidate with a different graph neighborhood, so the included
counterfactual demonstrates a true stage-A → intermediate → stage-B dependency.
Run `audit.py --out <new-directory>` for the protected-Racket finite-rival,
public-projection, and causal replay bundle.
