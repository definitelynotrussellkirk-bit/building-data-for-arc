# Solve work log

This is a human work log from the visible examples. I had earlier rule exposure while repairing the assigned generator, so this is not a blind record. During this solve episode I did not reopen the generator, Racket source, reference solution, or private labels.

## Hypothesis

The two full color-5 columns split each input into a source panel, its worked result, and a query panel. In each training example the middle panel is either:

- horizontal span closure: for every occupied row, fill between that row's leftmost and rightmost colored cells; or
- vertical span closure: for every occupied column, fill between that column's topmost and bottommost colored cells.

The source and worked panels reveal which of those two operations is active. Apply the same operation to the query, crop to the transformed object's bounding box, and recolor all occupied cells to 8 while retaining zero holes.

## Visible probes

- Example 0: source row 6 has colored cells separated by a gap; the worked panel fills the horizontal gap. The query output preserves a nonrectangular shape, ruling out simply filling the whole bounding box.
- Example 1: the worked panel fills vertical gaps within columns. Its query output is therefore column-closed.
- Example 2: the first source row has separated endpoints and the worked panel fills between them, confirming row closure even when the output is almost solid.

I implemented structural separator detection, compared both candidate closures to the worked panel, transformed the query, cropped it, and recolored it 8. No deliberate teaching-negative revision was needed.
