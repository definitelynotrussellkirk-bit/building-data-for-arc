# Solve notes

This is a human visible-example work log. I did not inspect the generator, Racket rule, reference solution, or private query labels during this solve phase. I had already seen the rule while repairing the generator, so this episode is exposed rather than blind.

## Hypothesis from the five demonstrations

The first row is a control strip:

- the count of leading blue `1` cells in columns 0–3 selects one of four 4×4 panels in reading order;
- column 5 is a transform code;
- column 7 is the output color.

The selected panel is cropped to its nonzero bounding box, transformed, and recolored uniformly. The demonstrations identify the complete transform table:

1. identity;
2. rotate 90° clockwise;
3. rotate 180°;
4. rotate 90° counter-clockwise;
5. reflect left-to-right.

The non-selected panels are distractors. Zeros remain background.

## Predicted queries

- Query 0 selects panel 2, uses code 1, and recolors with 8. Its predicted output is a 4×2 support: `[[8,8],[0,8],[0,8],[0,8]]`.
- Query 1 selects panel 3, uses code 2, and recolors with 3. Its predicted output is `[[0,3,3],[0,3,3],[3,3,0]]`.

The implementation encodes the general rule rather than these two predictions directly.
