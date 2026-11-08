# Blind solve notes — 69c39a5f416b

## Visible-only hypothesis

The first two rows form a vertical color-substitution key. At each column where
both cells are nonzero, the upper color maps to the lower color. The output
removes those two key rows, preserves the remaining geometry and background,
and replaces every keyed source color in the remaining rows by its paired target.

Evidence from the visible examples:

- Example 0 has `4→1`, `3→8`, `5→2`; every lower object is recolored accordingly.
- Example 1 allows separated key columns and has `6→1`, `1→6`, `9→2`, `3→8`.
- Example 2 has `4→9`, `9→4`, `8→5`, showing that the mapping may swap colors.
- Every visible output has exactly two fewer rows than its input and unchanged width.

## Implementation decision

Build the key from aligned nonzero cells in rows 0 and 1, then return a fresh copy
of rows 2 onward with keyed colors substituted. Unmapped values are preserved;
this keeps background zero unchanged and avoids assuming a contiguous key.

## Tests and alternatives

A visible-example harness was first run against the supplied placeholder and failed
with `NotImplementedError`, establishing the red test. The implementation is then
checked against all three visible training pairs. I considered detecting a blank
separator row, but rejected it: example 1 begins content immediately on row 2, and
the invariant supported by all visible pairs is specifically removal of two rows.
No generator source, rule source, prior solution, private label, or audit evidence
was consulted.
