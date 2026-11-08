# 32d6c6648427

11x11 0-bg grid encoding a BOOLEAN MOSAIC. Cell (1, 1) holds an OPERATION CODE: 1=AND, 2=OR, else=XOR. Two 3x3 ROW TEMPLATES sit at the top at columns (4, 8); two 3x3 COL TEMPLATES sit at the left at rows (4, 8). Each template is a binary mask painted in some non-0 color (the rule is color-blind: any non-0 cell = ON). Rule: for each col-template, hstack the cell-wise boolean combination (AND/OR/XOR per the op code) with each row-template; vstack the two rows into a 2x2 panel layout of 3x3 boolean results (8=true) with 1-cell gaps -> a 7x7 output. Color and exact template pattern are distractors; only the ON/OFF masks and the op code matter.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
