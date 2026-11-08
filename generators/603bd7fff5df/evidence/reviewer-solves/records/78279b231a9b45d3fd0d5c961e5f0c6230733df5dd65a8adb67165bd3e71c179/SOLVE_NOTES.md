# Blind solve: 603bd7fff5df

I used only the public presentation produced by `solve_episode.py blind prepare`
and `solve-blind/challenge.json`. I have not opened any task generator, canonical
rule, reference solution, task notes, audit records, or private labels in this
session. I have no known earlier exposure to this task.

## Observations and hypothesis

- Example 0 is 9 rows x 11 columns to 5 rows x 7 columns. Gray cells occupy
  rows 1..3 and columns 4..10. The output is input rows 0..4, columns 4..10.
- Example 1 is 9 x 9 to 5 x 5. Gray cells occupy rows 3..5 and columns 0..4.
  The output is input rows 2..6, columns 0..4.
- Example 2 is 11 x 13 to 6 x 5. Gray cells occupy rows 2..5 and columns 8..12.
  The output is input rows 1..6, columns 8..12.

My hypothesis is to crop to the gray bounding columns and to the gray bounding
rows extended by one row above and below. Preserve all cell values in this crop.
The azure scatter outside that rectangle is irrelevant.

## Visible-only probe

A Python probe computed the gray bounding box and compared two crops with each
visible output. The crop with the extra top/bottom row matches all three
examples. The tight gray bounding box matches none. This was hypothesis testing,
not a submitted failed solver revision. No deliberately wrong attempt was made.

## Revision 1

Implemented the crop directly. Boundary clipping and an unchanged return when
no gray cells exist are conservative extrapolations; the visible examples do
not establish behavior for missing gray markers. I will use the checker only
for visible-example and execution feedback. Query correctness remains unknown.
