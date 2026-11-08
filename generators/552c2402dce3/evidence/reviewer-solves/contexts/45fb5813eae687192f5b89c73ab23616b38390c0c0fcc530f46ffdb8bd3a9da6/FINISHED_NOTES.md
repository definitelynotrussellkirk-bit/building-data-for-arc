# Solve work log

Earlier exposure: I had not opened task `552c2402dce3`'s generator, canonical
rule, labels, solution, notes, or audit evidence in this packet. I do not recall
prior exposure elsewhere, but cannot prove that, so the final exposure field is
recorded conservatively.

## Visible pattern

Each changed region is an axis-aligned 2×2 window that initially contains three
azure (`8`) cells and one background (`0`) cell. The missing corner is filled.
Already complete 2×2 blocks and shapes that do not supply three corners are left
unchanged.

A critical disambiguation is that the operation is simultaneous/one-pass rather
than iterative. In train example 0, the component at rows 6–7, columns 5–7 gains
only `(7,6)`. Iterating would then create another three-corner window and also
fill `(7,5)`, which the shown output does not do. Therefore every decision is
made from the original input grid and written to a copy.

## Implementation and probes

Before implementation, importing the supplied skeleton and evaluating train
example 0 failed with `NotImplementedError`, establishing the expected red test.
The implementation scans every original 2×2 window, requires exactly three equal
nonzero values plus one zero, and fills that zero in the copied output. The
slightly color-generic condition preserves the visible rule while avoiding a
hard-coded `8`.

Expected query changes from the visible-only rule:

- Query 0: fill `(8,2)` and `(9,7)` only. Do not recursively fill `(9,2)`.
- Query 1: fill `(2,8)`, `(3,8)`, and `(6,3)`.

Remaining uncertainty is limited to whether unseen data could define background
or color semantics differently; all visible examples consistently use `0` as
background and `8` as the sole object color.
