# Solve notes for 056999828b88

This is a human work log, not a token-level model trace. I had already read the generator and task rule while performing the assigned generator review, so this solve is **not blind**. After `solve_episode.py prepare`, I consulted only `solve/challenge.json`; I did not reopen the generator, Racket authority, canonical source, reference solutions, or private labels.

## Visible-example observations

1. Each input contains three or four isolated, single-color, 4-connected objects on a zero background.
2. Every output preserves each object's shape and color after cropping away its surrounding background.
3. The cropped objects are placed left-to-right, aligned at their top bounding-box rows, with exactly one all-zero separator column.
4. The ordering matches increasing number of colored cells, not input scan order, color order, or bounding-box area:
   - Train 1 has object sizes 1, 2, 5, and 6, and the output uses that order.
   - Train 2 has sizes 1, 3, 5, and 6, again in ascending cell count even though the colors and positions do not follow that order.
   - Train 3 distinguishes the four-cell line from the five-cell cross and six-cell rectangle.
   - Train 4 includes a six-cell irregular object whose crop is placed after the smaller 2-, 3-, and 5-cell objects.
5. Output height is the maximum cropped-object height. Output width is the sum of cropped widths plus one separator column between adjacent objects.

## Hypothesis

Find same-color nonzero 4-connected components. For each component, compute its exact cell count and tight bounding-box crop. Sort crops by cell count ascending (color only as a deterministic tie-breaker), then concatenate them horizontally with one zero column between crops and top alignment.

## Implementation probe

I implemented the hypothesis directly in Python using a four-neighbor flood fill, normalized each component to its crop origin, and reconstructed the packed output. The first check is intended to test all four visible demonstrations and execution behavior. No alternate revision was needed unless visible feedback identifies a mismatch.
