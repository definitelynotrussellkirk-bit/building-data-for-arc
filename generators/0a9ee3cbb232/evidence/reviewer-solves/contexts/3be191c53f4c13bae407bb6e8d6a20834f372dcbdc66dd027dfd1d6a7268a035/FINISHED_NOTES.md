# Visible-only solve notes

## Exposure declaration

I had earlier exposure to the assigned generator family while repairing it, so this is **not** clean blind evidence. During this solve I did not reopen the generator, Racket rule, reference outputs, private labels, or previous solution explanations. I used only `WORK/solve/README.md`, `challenge.json`, and my own tests.

## Observations

Every output is a fixed 2×3 row-major tally. It contains a prefix of green `3` cells, then red `2` cells, then zero padding. Counts beyond six must therefore be clipped.

The visible examples distinguish how the two colors are counted:

- Green `3`: count maximal horizontal runs. The three training counts are 2, 4, and 3. In particular, vertically touching green bars still count once per row.
- Red `2`: count four-connected components. The three training counts are 2, 2, and 2. The second example is decisive: one isolated red bar plus a vertically connected 3×3 red block yields two, not four, red units.

Thus the transformation is: count green horizontal runs, then red four-connected components; write that many `3`s followed by that many `2`s into six row-major cells; pad with `0` and clip overflow.

## Alternatives rejected

- Count connected components for both colors: fails training examples 1 and 2 for green.
- Count horizontal runs for both colors: fails training example 1 for red.
- Count occupied rows or raw colored cells: fails multiple examples.
- Preserve spatial positions in the output: contradicted by the compact fixed-size tally.

## Query predictions

- Query 0 has five green horizontal runs and three red components. Clipping after six gives `[[3,3,3],[3,3,2]]`.
- Query 1 has four green horizontal runs and one red component, giving `[[3,3,3],[3,2,0]]`.

## Stopping reason

The hypothesis uniquely matches all three visible examples, including the asymmetric stacked-shape cases, and the implementation passes the frozen visible-example test.
