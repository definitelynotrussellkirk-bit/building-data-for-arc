# Solve work log

I had no earlier exposure to this task's generator, Racket rule, private labels,
or solution explanation. I used only the visible examples prepared in this folder.

## Revision 1 — row/column erasure with protected color 2

Hypothesis: each input `0` marks both its entire row and its entire column for
erasure. Every marked cell becomes `0`, except color `2`, which is protected and
remains unchanged. Cells outside all marked rows and columns also remain unchanged.

Evidence from the visible examples:

- Example 1 has four zeros in the final column. The output erases that column and
  all four corresponding rows, retaining every `2` on those lines.
- Example 2 has isolated zeros at `(12, 6)`, `(13, 0)`, and `(15, 11)`. Exactly
  rows 12, 13, 15 and columns 6, 0, 11 are erased, again except for `2` cells.
- Example 3's 2×2 zero block similarly erases its two rows and two columns.
- Example 0 initially looked like separate horizontal and vertical rays, but the
  union-of-rows-and-columns rule explains every changed cell uniformly.

Before implementation I ran a synthetic assertion against the placeholder
`solve`; it failed with `NotImplementedError`, as expected. The synthetic case
contains zeros in two rows and two columns and checks both ordinary erasure and
preservation of a `2`.

Implementation computes the sets of zero-bearing rows and columns, then applies
that mask without mutating the input. Remaining uncertainty is low: all visible
examples match the rule exactly, including dispersed and rectangular zero seeds.
