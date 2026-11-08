# Blind solve notes — 55cfa127936a

## Hypothesis
The output preserves exactly the topmost colored cell in every column and removes every colored cell below it. Empty columns remain empty. The color itself is copied unchanged.

## Evidence from visible examples
- Example 1: columns 0, 4, and 6 contain multiple yellow cells; only rows 2, 3, and 1 respectively survive, which are their topmost occurrences.
- Example 2: four full-height vertical stripes collapse to their four cells in the first row.
- Example 3: checking every populated column gives one survivor at its minimum row index; singleton columns are unchanged.

## Implementation
Scan each column from top to bottom, copy the first nonzero cell, then stop scanning that column. I used 0 as the background because every visible example uses 0 as background and 4 as the sole foreground color.
