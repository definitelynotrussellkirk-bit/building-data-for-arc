# Blind solve notes — a0c6005765ee

## Hypothesis 1

Each red cell (`7`) is immediately outside one side of a gray rectangular
frame (`5`).  It points straight through that frame.  Recolor every background
cell inside the rectangle on that row or column green (`3`), stopping at the
opposite gray side.  Leave the marker and frame unchanged.

Evidence:

- Example 0: the left marker points across the six-column frame and the four
  interior cells on its row become green.
- Example 1: the right marker points left through the smaller frame and its two
  interior cells become green.
- Example 2: each of two markers independently fills the aligned interior row
  of its own rectangle.

The same rule naturally covers top and bottom markers, which occur in test
query 0.  The implementation finds an adjacent gray cell, scans in that
direction to a second gray cell with a nonempty zero span, and fills the span.
No generator, rule, labels, or prior solution was consulted.
