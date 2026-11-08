# Blind solve notes — 9000d0ea6484

I used only `solve-blind/challenge.json` and local Python reasoning. I did not inspect any generator, Racket rule, canonical answer, prior solution, or audit record.

## Structural observation

Each input is four equal 4×4 panels separated by solid color-3 columns. Each panel contains one nonzero object color on a zero background. The output is a 4×4 overlay of those panels.

## Priority hypothesis

The overlay is not first- or last-nonzero. The demonstrations consistently imply a fixed panel priority (zero-based panel indices):

`2 > 3 > 0 > 1`

Evidence from training example 2:

- panel 2 beats panel 0 at row 1, column 2;
- panel 2 beats panel 1 at row 1, column 3;
- panel 2 beats panel 3 at row 2, column 1;
- panel 3 beats panel 1 at row 2, column 3;
- panel 3 beats panel 0 at row 3, column 3;
- panel 0 beats panel 1 at row 3, column 4.

This establishes a complete order, and examples 1 and 3 agree with it at every overlap. Empty cells remain zero. The separator color is structural and never enters the output.

## Implementation

Detect all-solid color-3 separator columns, split into four panels, then for each output cell take the first nonzero value in priority order `[2, 3, 0, 1]`.
