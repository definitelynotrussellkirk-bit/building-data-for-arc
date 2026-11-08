# Blind solve notes — e3f1bc75d654

Reference material was not consulted. I used only the visible examples produced by `review.py blind prepare`.

## Observations

- Every nonzero object has a rectangular bounding box and a single color.
- Most objects are hollow rectangular borders. Exactly one object per episode has a complete border plus a nontrivial interior pattern.
- The output keeps that patterned object and copies its relative occupied-cell mask into every hollow border with the same height and width, retaining each recipient's color.
- Objects whose bounding-box dimensions differ from the patterned source disappear.

Example checks:
- Train 0: the 6x7 color-7 pattern is copied to the 6x7 color-3 and color-5 frames; the 6x10 color-4 and 4x3 color-9 frames are removed.
- Train 1: the 6x5 color-4 pattern is copied into the 6x5 colors 3, 9, and 1; the 4x5 color-5 frame is removed.
- Train 2: the 8x6 color-3 pattern is copied into colors 7 and 6; differently sized colors 2 and 9 are removed.

## Implementation hypothesis

Find 4-connected monochromatic components. Select the unique component containing its entire bounding-box border plus at least one interior cell. Blank the canvas, then stamp that source mask (in each target's own color) at every complete-border component with identical dimensions. This also reconstructs the source itself.

## Expected queries

- Query 0: color 7 is the 7x8 source; stamp it into the 7x8 color-1 and color-3 frames, erase the 5x5 color-4 frame.
- Query 1: color 9 is the 8x5 source; stamp it into the 8x5 color-6, color-7, and color-8 frames; erase the 8x6 color-3 and 3x3 color-1 frames.

## Revision after visible check

The first implementation treated a monochromatic object as one 4-connected component. The checker passed only one of three visible examples. Direct comparison showed exactly three omitted cells in each failing example: one source-colored interior cell was disconnected from the border, and its copies were therefore also absent. The corrected representation uses a complete border component only to locate the bounding box, then includes every same-color cell enclosed by that border when forming the source mask.
