# Solve notes — `dd3fa537fa22`

## Exposure declaration

I had already studied and repaired this task's generator before this episode,
so this is **not blind**. During this solve episode I used only the four visible
training examples emitted by `solve_episode.py prepare`; I did not reopen the
generator, Racket authority, private labels, or the archived earlier solve.

## Visible-example rule

The input contains solid colored rectangles and cyan rectangular outlines.
Start from a fresh all-zero canvas. Preserve only cyan components that are
complete rectangular perimeters. For every solid non-cyan rectangle, find the
preserved frame whose *interior height and width* exactly equal that rectangle's
height and width, then fill the interior with the rectangle's color. Delete the
source rectangles, unmatched rectangles, and incomplete cyan candidates.

Train example 3 is decisive: its two inserts have equal area but transposed
ordered dimensions, and the frame order is crossed, so neither area nor screen
position is sufficient. Train example 2 shows that a cyan bounding box partly
overwritten by an insert is incomplete and must disappear rather than being
reconstructed.

## Implementation

The solver extracts monochromatic 4-connected components, recognizes a frame
only when its cell set equals the full perimeter of its bounding box, recognizes
an insert only when it fills its bounding box, and renders exact `(height,
width)` matches. This is the first genuine revision for this final episode.
