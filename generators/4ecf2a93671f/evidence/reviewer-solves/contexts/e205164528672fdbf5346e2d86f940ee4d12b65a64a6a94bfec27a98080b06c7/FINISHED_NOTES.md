# Solve work log

I had no earlier exposure to this task's generator, Racket rule, reference
solution, private labels, or prior solution notes. I used only the visible grids
created by `python3 review.py blind prepare`.

## Revision 1 — zero-mask Kronecker product

I partitioned each output into blocks the same size as the input. In train
example 1, the 3×3 binary pattern formed by the input's zero cells is

```
1 1 0
0 0 0
1 0 1
```

The output contains exactly this foreground-colored pattern in block positions
where the input is zero, and an all-zero block where the input is non-zero.
Train example 0 has three zero cells, so it produces three copies of a
three-pixel mask (nine foreground cells total). Train example 2 has five zero
cells and therefore produces five copies of a five-pixel mask (25 foreground
cells total). These counts and every visible block agree.

I implemented the result as the self-Kronecker product of the input zero mask,
colored with the sole non-zero input color. For an H×W input the output is
H²×W². I retained explicit loops rather than importing NumPy so the solve is
portable and easy to audit. The only remaining assumption is the visible one:
background is color 0 and there is one foreground color.
