# 9de65c6eed00 — normalized largest-minus-smaller mask difference

Two separated monochrome objects have unequal sizes. Normalize each object's
occupied cells to its own bounding-box top-left, subtract the smaller exact mask
from the larger mask, and paint the remaining cells in the larger object's color.
The output canvas uses the maximum normalized height and width of both objects.

The generator has a four-profile cyclic curriculum. It includes canonical subset
cases, non-subset overlaps, exact-mask-versus-bounding-box witnesses, and cases
where the smaller object's bounding box determines one output dimension. Every
advertised control is exact and recoverable from the returned grid.
