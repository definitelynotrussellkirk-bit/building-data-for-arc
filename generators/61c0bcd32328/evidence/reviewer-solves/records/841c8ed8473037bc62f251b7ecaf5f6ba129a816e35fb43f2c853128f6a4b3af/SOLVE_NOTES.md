# Solve work log

## Prior exposure

Before this blind solve I had read only the packet-level workflow documents and the
assignment text. I had not opened task `61c0bcd32328`'s generator, rule, notes,
solutions, audit records, or private labels.

## Visible-example observations and hypothesis

The dominant color is background. The changed cells can be explained by the
same operation in all three demonstrations:

- Find each monochrome 4-connected object whose bounding box touches the two
  outer borders belonging to a corner. The object need not occupy the literal
  corner cell; touching both borders is sufficient.
- Copy that object clockwise to the next corner: top-left to top-right,
  top-right to bottom-right, bottom-right to bottom-left, and bottom-left to
  top-left.
- Keep the object's orientation fixed in the global row/column frame. Translate
  its bounding box so that it touches the destination corner's two borders.
- Copy only the object's occupied cells. Do not erase the source. Incoming cells
  overwrite whatever was previously at the destination.

Concrete checks: in train 0 the top-left 2x2 color-4 block is copied unchanged to
the top-right; the top-right color-6 shape is translated to the bottom-right;
the bottom-right color-9 triomino is translated to the bottom-left; and the
bottom-left color-2 domino is translated to the top-left. The portions of old
corner objects not covered by the incoming shapes remain, which rules out a
move, rotation, or whole-corner replacement. Train 1 confirms that a lone
corner object is copied even when the other corners have none. Train 2 confirms
all four simultaneous copies and overwrite behavior.

I used same-color connectivity rather than treating all non-background cells as
one object because differently colored shapes can touch edge-to-edge (for
example, color 6 and color 8 in train 0) without moving together.

## Probe and implementation

Before implementing, I ran a local visible-example regression script against the
provided skeleton. It failed at `NotImplementedError`, establishing the expected
red state. I then implemented dominant-background detection, same-color
4-connected components, corner classification, and simultaneous clockwise
copying from the original grid.

Remaining uncertainty: the visible examples do not specify precedence if two
separate source components occupy the same corner and their translated copies
overlap. The generated examples appear to use at most one corner object per
corner, so the implementation follows deterministic row-major component order.
