# Blind solve: 2bb81826c18d

Earlier exposure: no. No generator, reference rule, canonical solutions, task notes, or private labels opened before this solve.

Visible inputs/outputs are respectively 17x15, 14x13, and 19x13. Each solid colored rectangle retains its one-cell border. Inside the rectangle, local coordinates (1,1), (1,3), (2,2), etc. are erased to background 0, producing a checkerboard whose phase resets per rectangle.

Hypothesis: find each orthogonally connected monochrome nonzero rectangle, preserve its border and erase interior cells with even local row+column. Global parity would give conflicting phases across the visible rectangles, so use each component's origin. Input/output shapes are unchanged in all visible examples. The query outputs and their dimensions remain unknown.

Implementation uses same-color connected components, allowing distinct disconnected rectangles to share a color. No revisions or deliberately incorrect attempts were needed before first checking. Plan: stop if all visible demonstrations pass and the queries execute, without inspecting withheld correctness.
