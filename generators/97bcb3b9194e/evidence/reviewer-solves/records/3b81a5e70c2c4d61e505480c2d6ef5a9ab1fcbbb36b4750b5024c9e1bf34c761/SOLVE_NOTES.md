# Blind solve notes — 97bcb3b9194e

## Visible-pattern hypothesis

The input contains several separated, solid rectangular objects on a zero background. Most cells in every object use the common base color `1`; a smaller number are marker/noise cells (`4` or `6`). The output is the complete crop of the object with the **fewest non-base cells**.

Visible counts supporting this:

- Training 1: candidate marker counts are 1, 3, and 3; the 1-marker 3×10 object is returned.
- Training 2: counts are 4, 2, and 4; the 2-marker 3×3 object is returned.
- Training 3: counts are 6, 5, and 3; the 3-marker 6×10 object is returned.

## Implementation

1. Infer the global background as the most frequent color.
2. Infer the common object-base color as the most frequent non-background color.
3. Find 4-connected non-background components.
4. Crop each component to its bounding box and count cells different from the base color.
5. Return the crop with the smallest count; use larger area and reading order only as deterministic tie-breakers.

This predicts test 1 selects the top-left 3×3 object (one marker), and test 2 selects the lower-left 8×10 object (two markers).
