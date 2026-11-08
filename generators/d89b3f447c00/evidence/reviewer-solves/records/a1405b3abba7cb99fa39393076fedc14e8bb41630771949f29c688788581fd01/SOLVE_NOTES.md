# Solve work log

## Prior exposure

Before this blind episode I had read only the packet-level instructions and the
assignment duties. I had not opened task `d89b3f447c00`'s generator, canonical
rule, reference solution, audit records, or private query labels.

## Revision 1 — complete the missing rectangle corner

Across all four visible examples, each changed cell completes an axis-aligned
rectangle whose other three corners already have the same nonzero color. A color
can also contain an unrelated distractor: color 5 in training example 1 and
color 7 in training example 2 each have four source cells, but only three form
the incomplete rectangle. Therefore counting all cells or taking a color's full
bounding box would be unsafe.

I implemented a non-cascading search over every pair of occupied rows and every
pair of occupied columns for each color. When exactly three of those four corner
coordinates contain the color and the fourth coordinate is background, the
solver fills the missing corner. Candidates are computed from the original grid
so one completion cannot manufacture another.

Expected query additions from this hypothesis:

- Query 0: color 6 at `(3, 0)` and color 2 at `(5, 8)`.
- Query 1: color 1 at `(3, 1)`, color 4 at `(0, 12)`, color 3 at `(5, 14)`,
  and color 6 at `(7, 4)`.

Remaining uncertainty: the visible data contains one intended incomplete
rectangle per color. The implementation completes every unambiguous three-corner
rectangle if a future grid contains several for one color.
