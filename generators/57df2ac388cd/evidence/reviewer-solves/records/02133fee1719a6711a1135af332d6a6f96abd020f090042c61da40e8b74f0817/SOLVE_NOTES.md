# Solve work log

## Exposure disclosure

Before this post-repair solve I had already inspected the selected task's generator,
canonical examples, and rule while repairing it. I did not reopen or consult those
sources after `review.py solve prepare`; this solve used the displayed challenge only.
The final finish record should therefore use `--earlier-exposure yes` and
`--reference-consulted no`.

## Revision 1

Visible examples contain two spatially separated monochrome objects. Their absolute
positions disappear in the output. Cropping each object to its own bounding box and
aligning both crops at `(0, 0)` reproduces every shown output: cells occupied by both
normalized objects become color 8, while cells occupied by only one retain that
object's color. Output dimensions are the maximum normalized height and width.

I implemented row-major object discovery, 4-connected monochrome components,
translation normalization, and the three-way overlay. The two query grids satisfy
the same visible structure. Remaining uncertainty is limited to the exact object
ordering convention; row-major first occurrence is consistent with all examples.
