# Visible-only solve notes — 504e304a77f1

## Exposure declaration

I had already reviewed this task's generator and canonical rule before this required post-repair episode, so earlier rule exposure is **yes**. During this solve episode I used only the visible examples printed by `review.py solve prepare`; I did not reopen the generator, Racket source, reference outputs, or private query labels.

## Hypothesis from the visible examples

The nonzero components split into hollow rectangular outline frames and ordinary colored shapes. The output erases each ordinary shape from its old location, keeps all frame outlines, and inserts the cropped shapes into frame interiors.

The pairing key is cell count for the ordinary shapes and interior area for the frames, both ascending. Train example 0 gives sizes 1, 3, and 4 going into the 1x1, 2x2, and 3x3 interiors. Train examples 1 and 2 include a useful disambiguation: a five-cell cross has a larger 3x3 bounding box than a six-cell 2x3 rectangle, yet the cross goes into the smaller-ranked frame, so rank is by cell count rather than bounding-box area.

Placement is centered independently in each frame using the cropped shape's bounding box; odd leftover margins use floor division for the top/left offset. Components are same-color 4-connected, which keeps same-colored but spatially separated frames distinct.

## Implementation

`solution.py` extracts same-color 4-connected components, recognizes exact hollow rectangular outlines, sorts the two component classes by the observed keys, paints the frames into a blank output, and centers each cropped shape into its paired frame. No query-specific coordinates or colors are hard-coded.
