# Solve work log

## Exposure declaration

Before this solve I had not opened task `e9238d278276`'s generator, Racket rule,
reference solutions, private labels, prior solve notes, or audit records. I used
only `solve-blind/challenge.json` and the public solve files. I had read the
packet-level instructions, which contain no task rule or solution.

## Revision 1 — independent upward column compaction

**Observation.** In every training pair, each output column contains exactly the
same nonzero values as the corresponding input column, in the same top-to-bottom
order. The only change is removal of zero gaps: the nonzero values begin at row
0 and all remaining cells below them are zero. Columns do not exchange values.
For example, in training example 1 column 0 changes from values `7,4` at rows
4–5 to `7,4` at rows 0–1; column 5 changes from `9,8` at rows 1–2 to rows 0–1.
The same pattern accounts for columns with one, two, and three values in the
other examples, including repeated colors.

**Hypothesis.** Apply upward gravity independently to every column, preserving
vertical order and the original grid dimensions.

**Alternatives considered.** Whole-object translation or row compaction cannot
explain why different columns move by different distances. Sorting colors cannot
explain preserved input order. Cropping is ruled out because output dimensions
are unchanged.

**Implementation.** For each column, collect nonzero cells from top to bottom,
write them starting at output row 0, and leave the rest zero.

**Remaining uncertainty.** None on the visible examples. The test cases contain
only rectangular grids and use 0 as background, matching all demonstrations.
