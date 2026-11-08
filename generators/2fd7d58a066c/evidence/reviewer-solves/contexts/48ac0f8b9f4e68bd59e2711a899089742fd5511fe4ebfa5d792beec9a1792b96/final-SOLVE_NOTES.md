# Fresh solve notes

These are a human-readable work log based only on `solve/challenge.json` after solve preparation. I had earlier rule exposure during generator review and will declare that honestly at finish. I did not consult the generator, Racket source, reference solutions, private labels, or earlier solution explanations during this solve phase.

## Visible observations

1. Output dimensions always equal input dimensions and the output background is always `0`.
2. Every output foreground cell is cyan (`8`), regardless of the input marker color.
3. Work appears independent by column. For each column containing input markers, the output covers every row from the highest marker through the lowest marker, inclusive.
4. Blank columns stay blank.
5. Adjacent occupied columns remain separate column operations; there is no horizontal bridge.
6. Training example 5 contains a singleton marker in column 1 at the last row. Its output is one cyan cell at that same position, so a one-marker column is a one-cell span.
7. Mixed colors do not define separate groups: training example 4 has different colors in column 1, yet one continuous cyan span is produced.

## Alternatives considered and rejected

- **Bounding rectangle around all markers:** rejected because outputs contain separate vertical bars and leave intervening columns blank.
- **Connect markers only when their colors agree:** rejected by mixed-color markers in the same column producing one span.
- **Require exactly two endpoints:** rejected by the singleton column and by columns with more than two visible markers.
- **Copy/recolor only existing markers:** rejected because blank cells between extremes become cyan.
- **Fill the full height of every occupied column:** rejected because cells above the topmost and below the bottommost marker remain background.

## Revision 1

Hypothesis: create a fresh zero grid; for each column with one or more nonzero input cells, find minimum and maximum occupied row and paint that inclusive interval with `8`.

Implementation: `solve/solution.py` scans each column, collects occupied rows, and paints the interval. The code also checks rectangularity to avoid silently returning malformed output.

Expected query behavior:

- Test 1 should create cyan spans in columns 0, 5, and 9.
- Test 2 should create cyan spans in columns 3, 4, and 7.

No failed code revision was needed because all five visible demonstrations support the same rule and explicitly falsify the strongest alternatives above.
