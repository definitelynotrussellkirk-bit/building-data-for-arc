# Blind solve notes — task 4296e507c770

## Visible structure

Each input has one multi-cell object in color 2 and four singleton markers in
colors 3, 4, 5, and 6. The output removes all source colors and stamps four
copies of the color-2 object's **tight bounding-box mask**, recolored 8. Each
singleton's location is the top-left corner of its stamped bounding box.

The three training pairs consistently encode these transforms:

- marker 3: unchanged mask;
- marker 4: left/right reflection;
- marker 5: top/bottom reflection;
- marker 6: 90-degree clockwise rotation.

The non-square template in training example 2 is the decisive probe: its color-6
copy changes from a 4x2 mask to a 2x4 mask, distinguishing rotation from a simple
reflection. The sparse first row/column patterns also fix the direction of each
reflection. Copies can coexist; filled cells are unioned as color 8 on a fresh
zero background.

## Revision 1

Implemented the bounding-box extraction, the four transforms, and stamping at
every visible marker. I chose clipping as a defensive boundary behavior, though
all visible instances appear generated to fit. No reference source, generator,
private label, or prior explanation was consulted.
