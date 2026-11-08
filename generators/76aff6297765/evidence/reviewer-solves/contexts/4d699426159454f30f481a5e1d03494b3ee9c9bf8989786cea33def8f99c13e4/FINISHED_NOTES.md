# Visible-only solve log

The input contains two equal-size panels separated by a complete row of 7s. The output has the panel dimensions, so the separator is structural rather than copied.

Across the visible examples, an output cell is 8 exactly when both vertically aligned input cells—one in the upper panel and one in the lower panel—are 0. The other three joint states (foreground/foreground, foreground/zero, zero/foreground) map to 0. This explains every visible output, including examples where both panels use the same foreground colour, so equality of raw cell values is not the rule.

Implementation plan: locate the unique full-7 row, split into equal-height panels, compare aligned cells, and emit 8 only for the double-zero relation. Validate rectangularity, unique separator, and equal panel heights rather than hard-code dimensions or colours.
