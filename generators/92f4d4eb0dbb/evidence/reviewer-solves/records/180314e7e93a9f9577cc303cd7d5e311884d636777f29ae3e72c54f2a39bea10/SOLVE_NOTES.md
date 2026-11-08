# Visible-only solve work log

This is a human-readable work log based only on the prepared visible examples. I had earlier exposure to the task rule while repairing the assigned generator, so this is not a blind solve; I did not consult the Racket source, generator source, private query labels, or prior solution explanation during this solve phase.

## Hypothesis

All examples preserve the grid and every non-1 cell. Let `top` and `bottom` be the minimum and maximum rows containing color 1. Color-1 cells strictly below the arithmetic midpoint `(top + bottom) / 2` become color 2; cells on or above the midpoint remain 1. This explains both even occupied heights (a half-integer split) and odd heights (the exact middle row remains 1).

## Implementation choice

Use the exact integer comparison `2 * row > top + bottom`, avoiding floating-point midpoint handling. Preserve the input unchanged if no color-1 cells exist, although every visible example contains them.
