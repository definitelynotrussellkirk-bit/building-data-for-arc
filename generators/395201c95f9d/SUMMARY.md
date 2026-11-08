# 395201c95f9d

Split the input at the two full-height color-9 columns into three equal panels.
The first two panels each contain a label at local `(0, 0)` and a monochrome
prototype shape. The third panel contains a translated rotation or reflection
of exactly one prototype. Return a blank panel of the same dimensions, keep the
query cells in their displayed positions, and recolor them with the matching
prototype's label color.

Version `3.1.0` generates D4-distinct prototype families, exercises all eight
D4 transforms, independently places the query, pins the selected rule hash, and
makes its panel size, cell count, match panel, and transform overrides exactly
observable.  Its 16-step curriculum crosses every transform with both matching
panels, and every four-example window includes rotation and reflection evidence
for both labels.
