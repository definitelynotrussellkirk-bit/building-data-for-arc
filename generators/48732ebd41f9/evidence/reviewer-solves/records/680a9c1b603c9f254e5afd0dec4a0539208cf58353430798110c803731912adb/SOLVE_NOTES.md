# Solve notes

## Visible evidence

Every changed cell is an input zero recolored to 6, and the changed cells form one solid axis-aligned rectangle. The four training rectangles are:

- example 0: rows 0–2, columns 11–13, area 9;
- example 1: rows 1–2, columns 3–5, area 6;
- example 2: rows 0–1, columns 5–9, area 10;
- example 3: rows 0–1, columns 13–16, area 8.

In each case the rectangle is entirely zero in the input and has height at least two. Competing zero runs exist, including a 4×2 block in example 0, but the selected rectangle has greater area. This rules out “widest,” “tallest,” and “first visually obvious gap” as the primary criterion.

## Hypothesis and implementation

Enumerate every row band of height at least two. For each band, intersect the zero columns across all rows, split that Boolean mask into contiguous runs, and choose the run/row-band rectangle with greatest area. Recolor that rectangle to 6 and preserve every other cell.

For an exact-area tie, use the first candidate in deterministic top-row, bottom-row, left-to-right scan order. The visible examples do not expose a tie, so tie behavior remains the only material uncertainty. The implementation returns an unchanged copy if no qualifying rectangle exists.

## Exposure declaration

This is a post-repair solve. I had already inspected the assigned generator family during the repair, so earlier rule exposure is **yes**. During this solve episode I used only the prepared visible examples and did not reopen generator, Racket, reference-output, or previous solution files.
