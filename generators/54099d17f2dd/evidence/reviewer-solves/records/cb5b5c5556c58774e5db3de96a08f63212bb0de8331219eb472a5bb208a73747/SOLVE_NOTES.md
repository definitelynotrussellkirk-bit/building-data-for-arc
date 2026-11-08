# Post-repair solve notes

This is a human work log from the visible examples. I had earlier rule exposure during the generator review, so this is **not blind**; during this solve I did not reopen the generator, Racket rule, reference solution, or private query labels.

## Visible evidence

- Train 0: Input 8×13, output 8×13. The five color-2 cells form a normalized zigzag. The output is the same normalized offsets in color 8, with its bounding-box top-left at the lone color-1 cell; all original cells disappear.
- Train 1: Input 9×11, output 9×11. A 2×2 color-2 block is copied to the color-1 location in color 8.
- Train 2: Input 9×12, output 9×12. The five-cell long L is copied without mirroring or rotation, anchored at color 1.
- Train 3: Input 9×12, output 9×12. A horizontal three-cell line is copied unchanged to color 1.

## Hypothesis

Find the color-2 template, normalize its cells by subtracting the minimum template row and column, create a fresh all-zero grid of the same shape, and stamp those offsets in color 8 with the unique color-1 cell as the new bounding-box top-left. Do not retain the source template or marker.

This directly distinguishes “move the object” from “copy while preserving source,” and Train 0/2 distinguish fixed-size tetromino assumptions. I implemented this rule once and stopped if all visible examples passed.
