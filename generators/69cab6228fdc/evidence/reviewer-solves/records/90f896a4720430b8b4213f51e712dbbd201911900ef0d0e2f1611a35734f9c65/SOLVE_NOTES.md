# Solve work log

I had no earlier exposure to task `69cab6228fdc`, its generator, or its rule. I used only the prepared visible examples.

## Revision 1 — vertical substitution legend

The first all-zero row consistently separates a two-row legend from the lower picture. In every nonzero legend column, the upper color maps to the lower color: example 0 gives `7→2`, `6→5`, and `3→8`; applying those substitutions to the five rows below the separator exactly reproduces the output. Example 1 similarly gives `9→5`, `6→2`, and `8→3`, while unlisted colors `4` and `7` remain unchanged. Example 2 confirms `1→3`, `4→9`, and `6→7`.

I implemented a generic parser that locates the first blank row, reads vertical source/destination pairs from the first two legend rows, removes the legend and separator, and substitutes only listed colors in the remaining grid. The main uncertainty is whether future instances could use more than two legend rows, but all visible examples support the two-row contract and the vertical-pair interpretation uniquely explains both the crop and recoloring.
