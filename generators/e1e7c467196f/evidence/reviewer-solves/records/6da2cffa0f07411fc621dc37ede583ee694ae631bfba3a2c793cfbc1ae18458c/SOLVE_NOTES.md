# Solve work log

## Exposure

Before this solve I read only the packet-level instructions and assignment duties. I did not open this task's generator, canonical rule, reference solution, private labels, notes, audit records, or the assigned repair generator. Earlier rule exposure: no. Reference consulted: no.

## Revision 1 — color-substitution legend

The top-left two-row nonzero rectangle acts as a legend. Its first row lists source colors and its second row lists corresponding replacement colors. The rest of the grid is the picture to transform. The legend cells disappear in the output, every occurrence of a source color outside the legend changes to its paired target color, and colors not listed as sources stay unchanged.

Evidence from the visible examples:

- Example 0 has legend `1 8 / 2 9`; all later 1s become 2s and all later 8s become 9s.
- Example 1 has legend `1 4 7 / 2 5 3`; later 1, 4, and 7 cells become 2, 5, and 3, while pre-existing 2 and 6 cells remain unchanged.
- Example 2 has legend `8 7 / 5 1`; later 8s become 5s and later 7s become 1s, while an existing non-source 1 remains 1.

The implementation finds the contiguous nonzero prefix of row 0, pairs it with row 1, erases exactly that 2-by-width legend, and applies a simultaneous one-step lookup to every other cell. Simultaneous lookup matters if a target color is itself also a source color; transformed values must not be transformed a second time.

Expected query behavior:

- Query 0 uses `3→7`, `9→2`, and `8→5`; the existing 2 outside the legend stays 2.
- Query 1 uses `6→2` and `9→3`.

Remaining uncertainty: the visible tasks always place the legend at the top-left, use nonzero source colors, and terminate the source row with background zero. The program deliberately follows that strongest common structure rather than guessing a more general legend detector unsupported by the examples.
