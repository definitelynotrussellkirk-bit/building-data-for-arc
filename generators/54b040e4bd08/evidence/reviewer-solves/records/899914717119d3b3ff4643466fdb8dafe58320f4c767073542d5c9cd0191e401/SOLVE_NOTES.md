# Solve work log

## Earlier exposure

Before this solve I had not opened task `54b040e4bd08`'s generator, canonical
rule, notes, reference solutions, audit evidence, or private labels. I used only
the examples printed by `python3 review.py blind prepare` and the solve template.

## Revision 1 — complete the periodic wallpaper

Each input is an otherwise complete two-dimensional periodic tiling with a run of
cells replaced by `0`. The output restores those holes; every existing nonzero
cell is unchanged.

Visible evidence:

- Example 0 alternates two row types and repeats every three columns. The damaged
  row's surviving endpoints identify the `[3, 7, 2]` row pattern.
- Example 1 repeats every three rows and two columns. Its damaged column is filled
  according to the same 3×2 tile.
- Example 2 repeats every two rows and three columns. The zeros in one row are
  exactly the missing continuation of `[8, 1, 7]`.

The implementation searches all row/column periods, rejects any period that
assigns conflicting observed nonzero values to the same tile position, and also
rejects periods that cannot determine a zero. It selects the smallest consistent
tile by area (then perimeter and dimensions) and fills only the zeros. Remaining
uncertainty: an intentionally non-minimal fundamental period could be ambiguous,
but all visible examples support the smallest-period interpretation.
