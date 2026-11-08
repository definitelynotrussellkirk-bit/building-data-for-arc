# Blind solve notes — ee6ef749efca

## Visible pattern

- Every input contains one or more magenta (`6`) components and isolated red (`2`) cells.
- The output removes the original objects and red cells.
- The largest 4-connected magenta component is normalized to the top-left of its bounding box.
- A copy of that normalized component is placed with its bounding-box top-left at every red cell.

## Evidence from the examples

- Example 1: the only magenta object is a five-cell cross. Each of the three red cells becomes the top-left anchor of a cross-sized 3×3 bounding box.
- Example 2: two magenta objects are present; only the larger four-cell T-like object is copied to both anchors, excluding the smaller three-cell object.
- Example 3: the larger four-cell L-like object is copied to all three anchors, including two nearby placements whose cells remain the union of the copies.

## Implementation choice

Use 4-connectivity to select the largest magenta component, normalize its coordinates, clear the canvas, and stamp it at each red coordinate. The generated examples keep every stamped cell in bounds; clipping is retained defensively.

## Test-instance prediction

- Test 1 stamps the two-row zigzag at anchors `(6,9)` and `(7,1)`.
- Test 2 stamps the same zigzag at anchors `(5,2)` and `(7,4)`.
