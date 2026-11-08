# Solve work log

## Prior exposure

This is the required post-repair solve. Before it began I had already inspected the assigned generator and canonical authority while repairing it, so earlier rule exposure is **yes**. After `solve prepare` I did not reopen the generator, Racket rule, canonical labels, reference solutions, or private query answers.

## Revision 1 — reflect vertically above the original

**Visible pattern.** Every output has twice the input height and the same width and color counts doubled. Its lower half is the input unchanged. Its upper half is the same rows in reverse order. In example 0, output rows 0–2 are input rows 2, 1, 0, followed by input rows 0, 1, 2. The 4×23 example shows the same construction at a noncanonical height, ruling out a fixed six-row output.

**Hypothesis.** Return the vertical flip of the entire input concatenated above the original input: `reverse_rows(grid) + grid`.

**Implementation.** Copy reversed rows, then copy the original rows, avoiding shared row references.

**Alternatives rejected from the visible examples.** Duplicating the input without flipping fails examples 0 and 2. Mirroring only a foreground object is unnecessary and would not explain why every cell, including the modal color, is duplicated in the same columns. A fixed three-row shortcut is contradicted by the four-row training example.

**Remaining uncertainty.** None within the visible family; the transformation is global and shape-independent. Private query labels remain intentionally withheld.
