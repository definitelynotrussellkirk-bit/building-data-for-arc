# Visible-only solve log

Human work log. I did not consult the generator, Racket source, reference output,
or earlier solution text during this solve phase. I had already reviewed the task
rule while repairing the generator, so this is an exposed post-repair solve.

## Hypothesis

The first column encodes row selectors by **color 1**. The first row encodes
column selectors by **color 2**. The output clears the entire input and puts 8 at
every Cartesian-product intersection of those selected rows and columns.

Role and color both matter: a color-2 mark in the first column (train examples 1
and 3) is ignored, and a color-1 mark in the first row (train example 2) is
ignored. This distinguishes the rule from "all nonzero border cells select."
All three visible outputs also show that source markers are erased rather than
preserved.

## Probe against visible examples

- Train 1: selected rows 1,3; selected columns 1,3,6,7, producing 2x4=8 cyan cells.
- Train 2: selected rows 1,2,4,5; selected columns 4,5,7; the top-row color 1 at
  column 2 is ignored, producing 4x3=12 cyan cells.
- Train 3: selected rows 1,2,5,6; selected columns 3,5,6,8; the left-column color
  2 at row 4 is ignored, producing 4x4=16 cyan cells.

A direct implementation should therefore scan exact border color/role pairs,
allocate a zero grid of identical shape, and paint their Cartesian product with 8.
