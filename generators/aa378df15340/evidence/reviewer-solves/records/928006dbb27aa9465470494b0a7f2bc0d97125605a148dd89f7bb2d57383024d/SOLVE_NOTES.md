# Post-repair solve notes

This is a human work log based only on the visible examples printed by `solve prepare`.
I had already seen the task rule while repairing the assigned generator, so this is
an exposed solve and will be declared with `earlier-exposure=yes`.

Hypothesis: the output preserves every colored input cell and adds its reflection
across the main diagonal. In coordinates, each nonzero `(row, col, color)` also
sets `(col, row)` to the same color. The visible examples include sources both
above and below the diagonal, which rules out an upper-triangle-only shortcut.
All visible source transposes are blank, so no overwrite convention is required.

Implementation: copy the grid, enumerate the original cells, and write each
nonzero value to the transposed coordinate. I used the original input as the
iteration source so newly added cells are not recursively processed.
