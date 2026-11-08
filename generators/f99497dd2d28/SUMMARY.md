# f99497dd2d28

0-bg grid (size varies) with one SHAPE in a single non-zero color (not 3). Half the time the shape is LR-symmetric with ODD bbox height; half the time it is asymmetric. Rule: find the mode non-bg color, crop to its bbox; if the crop is LR-symmetric AND (not UD-symmetric OR odd height) draw a full HORIZONTAL middle row of color 3 across the grid, otherwise draw a full VERTICAL middle column of color 3. The shape is preserved. So LR-symmetric odd-height shapes yield a horizontal 3-line; asymmetric shapes yield a vertical 3-line; the line sits at the grid's middle (which moves with the grid size). (Was a fixed 10x10 grid -> a single in/out shape.)

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
