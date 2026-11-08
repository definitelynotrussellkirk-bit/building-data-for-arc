# Solve notes — 2c784862f42b

## Visible observations

- Every input is 6×5. The upper 5×5 area is a one-color prototype.
- The last row contains four small integers followed by a different nonzero color.
- Every output is 5×23, exactly four 5×5 panels separated by three blank columns.
- The output preserves the prototype mask but recolors every occupied cell to the last-row color.
- Comparing successive panels shows that the four leading last-row values are operations applied to the **running** panel, not four independent operations on the original.

## Hypothesis used for revision 1

Decode the four operation values as: 0 identity, 1 rotate clockwise, 2 rotate 180°, 3 rotate counter-clockwise, 4 mirror left/right, 5 mirror up/down. Starting from the 5×5 prototype, apply each operation cumulatively. After every step, recolor occupied cells to the fifth last-row value. Concatenate the four recolored states left-to-right with one zero column between panels.

The three demonstrations collectively expose all six operation values, including identity and both reflection axes. No alternate rule was needed after checking panel dimensions and cumulative state transitions by hand.
