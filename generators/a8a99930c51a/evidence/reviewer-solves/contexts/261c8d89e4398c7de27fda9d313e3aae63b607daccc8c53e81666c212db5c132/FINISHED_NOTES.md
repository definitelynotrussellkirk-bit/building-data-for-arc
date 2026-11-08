# Solve notes

This is a human work log based only on the prepared visible examples. I had already seen the task rule while repairing the assigned generator, so this is an exposed post-repair solve, not a blind solve. I did not consult the Racket rule, generator source, reference solution, or masked labels during this solve phase.

## Hypothesis

The nonzero colors in row 0 form an ordered cyclic key from left to right. The key row itself stays unchanged. Below it, every occurrence of a key color is recolored to the next key color, wrapping the last color back to the first. Zero and colors absent from the key remain unchanged.

Visible checks:

- Example 0 key is `3 -> 9 -> 4 -> 3`; body 9 becomes 4, 3 becomes 9, and 4 becomes 3.
- Example 1 key is `5 -> 2 -> 9 -> 5`; the isolated color 8 is not in the key and remains 8.
- Example 2 key is `9 -> 3 -> 2 -> 9`, matching all three body objects.

The implementation reads row 0, builds that successor mapping, preserves row 0 verbatim, and applies the mapping only to later rows.
