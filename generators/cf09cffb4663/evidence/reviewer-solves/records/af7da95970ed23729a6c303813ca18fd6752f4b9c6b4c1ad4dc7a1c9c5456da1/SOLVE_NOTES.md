# Solve notes

This is a human work log based only on `solve/challenge.json` after episode preparation.

## Hypothesis

Across the three visible examples, the output preserves the grid and changes a blue
cell (`1`) to red (`2`) exactly where that cell has blue neighbors immediately above,
below, left, and right. Line length, connected-component size, and unrelated nearby
branches do not determine the mark: the second example marks both a compact plus and
a longer-line intersection, while the third leaves a near-corner branch unmarked.

## Implementation

Copy the input, scan interior cells, and recolor only cells satisfying the four-cardinal-
neighbor condition. Border cells cannot satisfy all four in-bounds neighbor tests.

No reference rule, generator source, private labels, or earlier solution explanation was
consulted during this solve phase. I had earlier exposure to the task rule while repairing
the generator, which will be declared honestly at finish.
