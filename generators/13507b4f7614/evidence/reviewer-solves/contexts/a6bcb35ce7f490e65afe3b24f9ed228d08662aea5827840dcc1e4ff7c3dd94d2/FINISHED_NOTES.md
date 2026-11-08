# Solve notes

This is a human-readable work log derived only from the visible examples shown by `prepare`.

## Hypothesis

Each 4-connected nonzero component is a filled rectangle. A rectangle whose height and width are both odd is reduced to the union of its middle row and middle column, preserving its color and location. A rectangle with either even dimension remains unchanged.

## Evidence from the visible demonstrations

- Train 0 contains two 3×3 rectangles; both become five-cell crosses.
- Train 1 is the branch-disambiguating example: the 5×5 rectangle becomes a cross, while the 4×2 rectangle is copied unchanged.
- Train 2 contains 5×5, 3×3, and 3×5 rectangles; all dimensions are odd, and all three become centered crosses.

## Implementation choice

Find 4-connected nonzero components, measure each component's bounding box, and apply the parity guard independently. Copy the input first so even-dimension components remain untouched. For an odd-by-odd component, erase its cells and paint the bounding box's middle row and middle column.

## Limitations considered

The visible examples use one foreground color and solid separated rectangles. The solution preserves each component's observed color rather than hard-coding 4, but it assumes components are rectangle-shaped as shown. No reference implementation, generator source, private query label, or Racket rule was consulted during this solve episode.
