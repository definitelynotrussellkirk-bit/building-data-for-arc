# Solve work log

## Exposure record

Before this solve I had already inspected and repaired the assigned generator and had seen the task's authoritative transformation. I therefore record earlier rule exposure as **yes**. During this solve episode I did not reopen the generator, Racket rule, canonical solution, private labels, or earlier solution notes; I used only the visible examples in `WORK/solve/README.md` / `challenge.json`.

## Revision 1

**Visible pattern.** Every nonzero color appearing exactly twice is replaced by its filled axis-aligned bounding rectangle on an otherwise zero grid. A nonzero color with a count other than two is omitted: train example 1 removes the singleton 4, and train example 2 removes the three cells of color 2. Both diagonal orientations occur, and examples contain more than two qualifying colors, so neither orientation nor pair count is part of the rule.

**Implementation.** Collect coordinates by nonzero color. For each color with exactly two coordinates, fill all rows and columns between the endpoints, inclusive, into a fresh zero grid of the input shape.

**Alternatives rejected from visible evidence.** Copying the input before filling would preserve singleton/triple decoys, which the outputs do not. Filling every color's bounding box would also preserve/fill those decoys. Restricting to backslash diagonals is contradicted by train examples containing slash-oriented endpoint pairs. Restricting to two qualifying colors is contradicted by train examples 1 and 2.

**Remaining uncertainty.** Visible execution can establish only agreement with the four training examples. Private query correctness remains withheld by the episode protocol.
