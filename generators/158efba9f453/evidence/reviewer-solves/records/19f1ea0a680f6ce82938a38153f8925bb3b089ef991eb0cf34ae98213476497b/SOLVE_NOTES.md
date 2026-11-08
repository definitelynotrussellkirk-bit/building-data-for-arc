# Solve work log

## Exposure record

Before this solve episode I had already inspected the selected generator and
Racket-backed rule while repairing the task, so earlier exposure is **yes**.
During this isolated solve I did **not** reopen the generator, Racket rule,
reference solutions, private query labels, or prior solution explanations.  I
used only `solve/README.md`, `solve/challenge.json`, my own implementation, and
the public check command.

## Visible observations

All three training pairs preserve the grid dimensions and the complete input.
Each input has two gray (`5`) cells in one column.  Colored motif cells are
copied to equal row positions on the opposite side of that column: a source at
column `c` is copied to `2 * axis_column - c`.  Cells already on the axis map to
themselves, and the gray marker cells remain unchanged.

The examples include sources on both sides of the marker column, so the rule is
not “copy left to right only.”  The marker column is also not necessarily the
geometric center of the whole grid.

## Implemented hypothesis and probe

I implemented a pure `solve(grid)` that:

1. checks that the grid is rectangular;
2. derives the single marker column from all gray cells;
3. copies the input;
4. reflects every nonzero, non-gray cell across that column using the original
   input as the source.

I then used `solve_episode.py check` against every visible training pair.  The
first implementation is intended to be the only revision unless that check
reveals a visible mismatch.

## Alternatives rejected

- reflecting around the geometric center: contradicted by examples where the
  gray column is off-center;
- horizontal reflection: contradicted by unchanged row coordinates;
- moving motifs instead of copying them: contradicted by preservation of the
  source cells;
- reflecting only left-side motifs: contradicted by the second training pair,
  whose visible motifs lie to the right of the gray column;
- filling the gap or bounding box: contradicted by sparse shapes remaining
  sparse after reflection.

## Remaining uncertainty

Private query outputs are deliberately withheld, so visible-example success is
not a direct private-label check.  The two queries have the same marker and
motif structure as the demonstrations, and no visible evidence supports an
additional condition.
