# Visible-only solve notes

## Hypothesis

The 7-cells form the rectangular room boundary, with occasional 7-cell obstacles inside it. Every other nonzero interior cell is a color seed. Fill each interior zero with the color of the seed having minimum Manhattan distance; when distances tie, choose the numerically smaller color. Preserve all existing cells and all zeros outside the room.

## Evidence from the demonstrations

- Example 2 gives large axis-aligned regions exactly matching Manhattan nearest-seed cells for seeds 3, 1, and 5.
- Example 3 distinguishes the tie rule: cell `(4,5)` is equally distant from colors 2 and 9 and becomes 2.
- Example 1 has several multiway ties; `(5,2)` is distance 2 from colors 4, 5, and 6 and becomes 4. Its internal 7 at `(5,3)` does not block distance, so 7-cells are preserved masks rather than path barriers.

## Implementation

Find the bounding box of color 7, collect nonzero/non-7 seeds strictly inside it, and assign each interior zero by `(Manhattan distance, color)` lexicographic minimum.
