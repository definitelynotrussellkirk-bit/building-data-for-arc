# Visible-only solve notes

This is a human-authored work log. I had earlier rule exposure from repairing the selected generator, so this episode is not blind; during this solve I used only the visible examples printed by `solve prepare` and did not reopen the generator, Racket rule, canonical answers, or private labels.

## Hypothesis

Color-9 full rows and columns partition each input into 3×3 tiles. Count the occupied (nonzero) cells separately in every tile. The output preserves every cell except that all occupied cells in the uniquely densest tile become color 8.

Visible checks:

- Example 0 has tile occupancies 2, 5, 4, 3; only the five-cell tile changes.
- Example 1 has no five-cell tile. Its unique maximum has four occupied cells and that tile changes, ruling out a fixed-five shortcut.
- Example 2 has a unique seven-cell maximum and a separate five-cell tile; only the seven-cell tile changes.

The implementation finds full color-9 divider lines rather than assuming a fixed lattice size, forms the intervening rectangular tiles, selects the unique maximum occupancy, copies the grid, and recolors that tile's nonzero cells to 8.
