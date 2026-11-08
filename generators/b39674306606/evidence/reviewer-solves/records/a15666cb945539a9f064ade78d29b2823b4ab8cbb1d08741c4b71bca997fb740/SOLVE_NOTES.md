# Blind solve notes

The grids contain several disconnected monochrome objects. The output removes all
objects except one and recolors the retained cells 8.

Hypothesis: compare each object's normalized coordinates without allowing rotation
or reflection. Repeated oriented shapes are decoys. Keep the first object in
row-major order whose oriented shape occurs exactly once. This explains the paired
3x3 blocks and bars in example 1, the paired horizontal zigzags in example 2, and
the selected earliest singleton in example 0 (where another later singleton is
present). Query 0 appears to leave a unique 2x2 square after paired L and T shapes;
query 1 leaves the color-1 object after paired six-cell and 2x2 shapes.
