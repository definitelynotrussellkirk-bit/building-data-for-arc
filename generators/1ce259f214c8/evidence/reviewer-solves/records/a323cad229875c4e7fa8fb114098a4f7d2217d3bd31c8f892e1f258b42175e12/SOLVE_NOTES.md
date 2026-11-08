# Blind solve notes — task `1ce259f214c8`

## Exposure declaration

I examined only `solve-blind/challenge.json` while deriving the rule. I did not
open the generator, Racket rule, canonical record, prior solutions, private
labels, or audit material for this task.

## Observations

- Every input is two equal-height, equal-width panels separated by a full column
  of color 5.
- The two panels use different foreground colors, but the output uses only 0 and
  8 and has the dimensions of one panel.
- In training example 2, comparing the panels cell by cell gives output 8 exactly
  where one side is foreground and the other is background:
  - row 2: `01010 XOR 01110 = 00100`
  - row 3: `01110 XOR 00110 = 01000`
  - row 4: `01110 XOR 00010 = 01100`
  These match the visible output rows.
- Direct cellwise XOR of foreground occupancy also reproduces all rows of the
  other four examples. No reflection, rotation, or color-specific mapping is
  needed.

## Hypothesis

Split at the solid color-5 separator. For each aligned cell, output color 8 if
exactly one panel cell is nonzero; otherwise output 0. This is the symmetric
difference (boolean XOR) of the two foreground masks.

## Implementation choice

The solver locates the unique full-height color-5 column instead of assuming a
fixed index, checks that the flanking panels have equal width, and applies the
occupancy XOR. Foreground colors are intentionally treated generically because
the examples vary them.

## Alternatives rejected

- **Union:** would retain cells occupied in both panels, contradicted by example
  2 row 2 column 2.
- **Intersection:** would omit the many one-sided cells that become 8.
- **Panel subtraction in one direction:** both left-only and right-only cells
  become 8, so the operation is symmetric.
- **Geometric transform before combining:** direct alignment already matches all
  five examples exactly.
