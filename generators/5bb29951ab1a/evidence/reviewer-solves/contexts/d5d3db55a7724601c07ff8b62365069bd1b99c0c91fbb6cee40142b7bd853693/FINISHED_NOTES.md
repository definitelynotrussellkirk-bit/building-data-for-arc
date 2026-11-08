# Visible-only solve notes

- All four demonstrations contain background 0 and exactly two nonzero colors.
- The frequent color forms filled rectangles separated by one-cell gutters; the sparse color marks candidate cells both inside rectangles and outside them.
- Comparing input/output cell by cell, every sparse marker disappears unless at least two of its four orthogonal neighbors are the frequent rectangle color. Markers meeting that threshold become the rectangle color.
- This explains internal holes/corner notches and the straight bridge examples, while one-neighbor and isolated markers become 0.
- Neighbor counts must be taken from the original input simultaneously, because changing one sparse cell must not affect another's classification.
- Role inference: choose the more frequent nonzero color as the rectangle color and the other as the sparse marker color.
