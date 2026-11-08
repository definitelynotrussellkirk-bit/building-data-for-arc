# Solve work log

This is a human work log. I had already inspected the canonical rule while repairing the generator, so this is an **exposed** post-repair solve, not a blind solve. During this solve phase I did not reopen the Racket rule, generator implementation, reference solutions, or private query labels; I used only `solve/challenge.json`, the printed visible examples, and local Python tests.

## Preparation history

The first preparation attempt, bound to generator SHA-256 `ce5569452b8cbd1a5bbd3296e27f08af7ac276b68760e623c1790703eed557ff`, failed during public episode validation because some Racket-labelled cells were Python booleans. That genuine failure is retained under `prepare-failures/0001.json`. After the generator repair removed unsupported unpaired-dot scenes, preparation succeeded from final generator SHA-256 `160bcb93f94f83245ca71cc744747025542c0eaa1e99336461ee4f9029e45ac3`.

## Revision 1 hypothesis

Across the five visible examples, every nonzero input point has exactly one other nonzero point in its row. The output appears to:

1. Replace each point by a clipped 3×3 block whose center keeps the point's own color and whose eight surrounding cells use the same-row partner's color.
2. Connect every pair of points sharing a row or column with color-5 dots spaced every two cells, grown independently from both endpoints toward the midpoint. This explains the adjacent middle pair for odd endpoint distances and the single shared midpoint for suitable even distances.
3. Draw the 3×3 blocks first and the color-5 guides second.

I first wrote `test_solution.py` against all five visible train examples. It failed with `NotImplementedError`; that RED run is retained in `checks/solve-tdd-red.log`. I then implemented the hypothesis in `solution.py`. The visible regression passed 1/1 test over all 5 examples (`checks/solve-tdd-green.log`).

## Alternatives rejected

- A single alternating parity from the left endpoint cannot explain odd-distance examples, where guide dots approach from both ends and create two central dots of opposite parity.
- Filling block rings with the point's own color contradicts examples where a diagonal rectangle swaps colors across each row.
- Connecting only rectangle-adjacent points is unnecessary; the visible rule is expressible directly as all row- or column-aligned pairs.

## Remaining uncertainty

The check command exposes only visible-example execution, so private query correctness remains withheld. The implementation deliberately follows the structures shown in the prepared episode: rectangular grids, integer colors, and a same-row partner for every nonzero point.
