# Solve work log

## Prior exposure

This solve was started immediately after the assignment draw. I had not opened
this task's generator, Racket rule, canonical record, prior review material, or
private labels. I had read only packet-level instructions before opening the
visible `challenge.json`.

## Revision 1 — orthogonal emitters separated by gray walls

**Observation.** Each singleton color other than 5 expands along its row and
column. Gray 5 cells remain fixed and terminate expansion. For example, in the
first training pair, color 3 at row 2 / column 5 fills left and right only as far
as the gray cells at columns 2 and 8, and fills downward only as far as the gray
cell in row 5. Color 4 behaves the same way from its own seed.

**Intersection hypothesis.** Empty cells reached by two or more colored
projections become 8. Original colored seeds remain their original color even
when another projection passes through them; projections continue beyond such a
seed. The second training pair makes this visible: colors 1 and 7 share a row,
so the empty cells on both sides and between them are 8, while the seed cells
remain 1 and 7.

**Implementation.** Enumerate every nonzero/non-5 seed, cast four rays until a
5 or boundary, collect source hits only on originally empty cells, then assign a
single source's color or 8 for multiple sources. Preserve all original nonzero
cells.

**Alternatives considered.** I briefly checked whether 8 might mark only
perpendicular crossings. The collinear 1/7 overlap in training pair 2 rules that
out: collinear overlap also becomes 8. I also checked whether colored seeds block
rays; the 8 cells beyond the two same-row seeds rule that out.

**Remaining uncertainty.** The examples use one seed per color, so they do not
show whether overlapping rays from two seeds of the same color should stay that
color or become 8. I track distinct emitters, which matches the apparent
"multiple projections" semantics; this does not affect any visible instance.
