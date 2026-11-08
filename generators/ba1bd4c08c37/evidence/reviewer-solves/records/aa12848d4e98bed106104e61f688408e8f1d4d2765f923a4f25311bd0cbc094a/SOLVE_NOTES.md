# Visible-only solve notes

The demonstrations contain one nonzero figure whose bounding box is symmetric across both axes. The output preserves colors and internal zeros, and is exactly the upper-left half in each bbox dimension. Canvas placement is irrelevant: locate the nonzero bounding box, take floor(height/2) rows and floor(width/2) columns starting at its top-left, and return that crop. This also explains the rectangular 6x10 -> 3x5 and 10x6 -> 5x3 demonstrations, ruling out a fixed 4x4 crop.
