# Post-repair visible-only solve notes

## Hypothesis

The dominant nonzero color is the field/background; zero can be a real object.
Find each monochromatic four-connected component outside that field. A component
whose bounding box is the entire canvas is a disposable surrounding frame.
Sort the remaining objects by number of occupied cells, then preserve each
object's shape inside its bounding box while placing the boxes left-to-right,
flush to the bottom, with no inter-box gap. Fill all other cells with the field
color.

## Checks against the demonstrations

- Example 0 orders cell counts 3, 4, 6, 11 and gives bounding-box starts at
  columns 0, 2, 4, 5.
- Example 1 uses color 6 as the field even though color 5 forms a border. The
  whole-canvas border is removed, then sizes 3, 5, 6, 13 are bottom-packed.
- Example 2 confirms that a zero-colored component is retained and sorted by
  its two occupied cells rather than treated as empty space.

The two queries exercise both frame removal and ordinary frameless packing. The
implementation follows only the visible examples. I had earlier exposure to the
general task rule while repairing the generator, but did not consult generator
or reference source after preparing this episode.
