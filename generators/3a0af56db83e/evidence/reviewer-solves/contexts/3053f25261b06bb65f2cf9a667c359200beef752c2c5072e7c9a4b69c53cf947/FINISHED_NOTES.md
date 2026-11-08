# Solve work log

Earlier exposure: I had not seen task `3a0af56db83e`, its rule, generator, solutions, labels, or prior explanations before this blind episode. I read only `solve-blind/challenge.json` and the packet-level solve instructions.

## Revision 1 — four-panel overlay with a nontrivial last-two order

The 12-row input is four vertically stacked 3-row masks, each drawn in a different nonzero color. The output has the same width and three rows, so I compared collisions at each output coordinate across the four aligned masks.

Across all three visible examples, the winning panel order is consistent: first panel beats every later panel; second beats panels three and four; fourth beats third. Equivalently, the precedence is panel 1 > panel 2 > panel 4 > panel 3. For example, in training example 2 at row 1, column 7, panels 2, 3, and 4 contain 4, 5, and 8, while the output is 4; at row 1, column 3, panels 3 and 4 contain 5 and 8, while the output is 8. This rules out ordinary top-to-bottom overlay and supports swapping the final two priority levels.

Implementation: split the grid into four equal-height panels, start with zeros, then paint nonzero cells from lowest to highest priority in panel order 3, 4, 2, 1 (zero-based indices 2, 3, 1, 0). The code supports any common panel height, not only three rows.

Remaining uncertainty: the visible examples establish the priority pattern but do not explain a higher-level semantic reason for the last-two swap. The implementation follows the exact invariant shared by every visible pair.
