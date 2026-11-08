# Solve notes

## Hypothesis

The unique gray cell (`5`) is a pivot. Every other nonzero input cell remains in place and is copied to the coordinate obtained by a 180-degree rotation around that pivot:

`(r, c) -> (2*pivot_row-r, 2*pivot_col-c)`.

The first two demonstrations show the source above the pivot and its antipodal copy below. The third and fourth demonstrations are decisive: source cells occur on axes and on multiple sides of an off-center pivot, while the output adds every missing antipodal partner. Colors are preserved and the original source is not erased.

## Implementation

Find exactly one `5`, deep-copy the input, then iterate only over the original input cells. For each color other than `0` and `5`, write the same color at its antipode when in bounds. Iterating the original rather than the growing output prevents copied cells from being copied again.

## Exposure declaration

This is the required post-repair solve. I had already inspected and repaired this task's generator/rule before preparation, so earlier exposure must be recorded as `yes`. During this solve phase I used only the visible examples and did not reopen the generator, Racket source, reference solution, or private labels.
