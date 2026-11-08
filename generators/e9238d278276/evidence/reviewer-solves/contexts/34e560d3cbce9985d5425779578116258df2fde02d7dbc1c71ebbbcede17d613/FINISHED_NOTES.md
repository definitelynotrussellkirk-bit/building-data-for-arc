# Solve work log

## Exposure declaration before solving

I had not opened task `e9238d278276`'s generator, Racket rule, private labels,
reference solutions, earlier solution notes, or audit records. I used only
`solve-blind/challenge.json` and the public solve/check interface.

## Revision 1 — stable upward compression by column

### Observation

Across all four training pairs, the set of colored cells in each column is
unchanged, while all empty cells beneath them are discarded from the column's
active prefix. Reading each input column from top to bottom and deleting zeros
exactly yields the nonzero prefix of the corresponding output column.
Examples:

- Training 1, column 2 has `5, 4` in that order and becomes rows 0–1 `5, 4`.
- Training 2, column 3 has `4, 6, 8` and becomes rows 0–2 `4, 6, 8`.
- Training 3, column 0 has `5, 2, 1` and becomes rows 0–2 `5, 2, 1`.
- Training 4, column 6 has duplicate values `4, 4`; both are retained, showing
  that this is movement/compression rather than deduplication.

### Hypothesis

Apply upward gravity independently to every column: gather its nonzero values in
original top-to-bottom order, place them starting at row 0, and fill the rest of
the column with zero. Grid dimensions and colors stay unchanged.

### Alternatives considered

A global row sort or packing colored cells into a bounding box would not preserve
the observed column assignments. Sorting colors numerically would also fail
columns such as `5, 2, 1`, whose order remains unchanged. The duplicate `4, 4`
case rules out set-based collection.

### Program

`solution.py` implements stable per-column nonzero compaction. I expect both test
inputs to retain their dimensions and each column's exact nonzero sequence, moved
to the top.

### Remaining uncertainty before check

Only the visible examples establish the direction and independence of motion.
The rule is nevertheless exact on every visible pair and has no unresolved
special case for empty columns or duplicate colors.

## Check result

Revision 1 executed successfully and matched all 4 of 4 visible training outputs.
No revision was needed. Masked test correctness remains intentionally withheld,
so I stopped because the single rule explains every visible transformation with
no exceptions or extra parameters.
