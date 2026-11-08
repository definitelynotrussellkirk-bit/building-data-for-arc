# Visible-only solve notes

This is a human work log. I had earlier rule exposure from reviewing the assigned
generator, so this episode is not blind. During this solve phase I consulted only
`solve/challenge.json`; I did not reopen the generator, Racket rule, reference
solutions, private labels, or previous solution explanations.

## Hypothesis from the four visible demonstrations

The top-left nonzero value behaves as a one-based rank and is removed before
object analysis. The remaining nonzero cells form monochrome 4-connected
components, including separate components that may share a color.

The examples identify the complete ordering:

1. Sort components by occupied-cell count descending. Training example 1 uses
   rank 2 to select the four-cell square between a five-cell object and a
   three-cell bar.
2. Break equal-size ties by leftmost column ascending. Training example 2 has
   two four-cell objects; rank 2 selects the left one.
3. If size and leftmost column still tie, use color ascending. Training example
   3 has two four-cell objects beginning in the same column; rank 2 selects
   color 2 rather than color 9.
4. Return the inclusive bounding-box crop from the marker-cleared grid, retaining
   any internal zeros. Training example 4 also shows that disconnected objects
   of the same color remain separate objects.

I implemented a same-color BFS, the three-key ordering
`(-cell_count, left_column, color)`, and an input-pure crop. No alternative rule
survived all four visible demonstrations, so I stopped after the first checked
solution.
