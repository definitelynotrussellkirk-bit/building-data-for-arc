# Blind solve notes — 59c2f0a5d4a9

## Visible-pattern hypothesis

The color-1 pixels form hollow axis-aligned rectangular frames. A color-2 pixel
inside a frame selects that frame. For every selected frame, replace its entire
interior (zeros and any 2 markers) with color 4. Leave unselected frames and all
color-2 pixels outside frames unchanged.

Evidence from the three visible examples:

- Example 1 fills only the small frame containing one interior 2; the larger
  marker-free frame stays hollow.
- Example 2 fills both lower frames because each has an interior 2, while the two
  upper marker-free frames remain unchanged.
- Example 3 fills the large left frame containing interior 2s. The 2 immediately
  outside its left border and the isolated lower 2s remain 2, and the right
  marker-free frame remains hollow.

## Implementation probe

Find 4-connected components of color 1, verify each component's bounding-box
perimeter is a complete rectangle, inspect only the strict interior for a 2, and
fill that strict interior with 4 when selected. This avoids treating exterior
markers adjacent to a frame as selectors.
