# Solve work log

## Prior exposure

Before this visible-only episode I had already reviewed the assigned generator and its canonical rule, so earlier rule exposure is **yes**. During this solve I did not reopen or consult the Racket rule, generator implementation, reference solutions, private query labels, or earlier solve records; I used the printed examples and `challenge.json` only.

## Visible hypothesis

Across all three demonstrations the most frequent color acts as background. Exactly two columns are entirely background, splitting the canvas into three vertical regions. Each region contains one distinct foreground color plus background holes. The separator columns stay unchanged, while every background hole in region 0 is filled with region 1's color, region 1 holes receive region 2's color, and region 2 holes receive region 0's color.

I checked this against the visible examples: in example 1 the all-zero columns split foreground colors 9, 8, and 3; the output fills their holes with 8, 3, and 9 respectively. The same spatial cycle explains examples 0 and 2 despite different background and palette values, ruling out a fixed-color or numeric-order mapping.

## Implementation

`solution.py` identifies the modal background, finds full-background separator columns, groups the remaining columns into regions, extracts the unique non-background color in each region, and fills only that region's background cells with the next region color cyclically. It preserves separator columns and all existing foreground cells.

Remaining uncertainty before the visible check was limited to whether the region cycle was spatial-next versus numeric-color order; the examples with arbitrary palettes support spatial-next.
