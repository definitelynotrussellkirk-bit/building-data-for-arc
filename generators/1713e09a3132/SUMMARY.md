# 1713e09a3132

Each nonzero color appears at two diagonal corners. Draw the border of each color's bounding box in first-reading-order color order; later borders overwrite earlier borders at intersections.

The native generator now covers one to four pairs, both diagonal orientations, full declared grid boundaries, spans of eight or more, and overlapping bounding boxes. Overlap is lawful and is no longer rejected by `self_check`.
