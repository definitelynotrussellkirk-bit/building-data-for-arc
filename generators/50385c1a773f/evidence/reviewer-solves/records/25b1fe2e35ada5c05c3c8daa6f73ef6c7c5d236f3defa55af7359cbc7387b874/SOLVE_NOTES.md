# Blind solve notes — 50385c1a773f

Prior exposure: none known. I read only the prepared visible challenge before writing this solution.

## Observations

- Color 2 is the start of a rectilinear path.
- Other colored singleton cells (3 or 4) are waypoints. Consecutive waypoints are axis-aligned, and the output fills only the zero-valued cells between them with color 8.
- A terminal waypoint connects to a color-5 object when one is axis-aligned.
- When no color-5 cell is axis-aligned, the 5-object indicates the side of the terminal waypoint for a perpendicular ray, and that ray continues to the grid boundary.
- Existing nonzero cells are preserved.

## Alternatives considered

I considered treating 3 and 4 as fixed direction codes, but the third training example instead supports a waypoint chain: 2→4 horizontally, 4→3 vertically, then 3→5 horizontally. I also considered connecting every aligned 5-object to color 2, but training example 2 leaves the grey component to the left of the start untouched. The path therefore begins at 2 and proceeds forward through colored waypoints.

## First implementation

Follow aligned unused colored waypoints from 2, painting gaps with 8. Then connect the terminal waypoint to the nearest aligned 5 cell. If no 5 is aligned, continue perpendicular to the previous segment toward the side containing the grey cells, up to the edge. This directly predicts both held-out inputs: each is a 2→4 horizontal segment followed by a downward 4→5 segment.
