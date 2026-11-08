# Post-repair visible-only solve notes

## Revision 1

Across all three demonstrations, every changed cell is the sole zero in a 2×2
window whose other three cells have one common nonzero color. The output copies
that color into the missing corner. Unrelated zeros, already complete regions,
and mixed-color near-matches remain unchanged.

I will scan every 2×2 window in the original input and write qualifying missing
corners into a copied output. Reading evidence from the original input matters:
newly filled corners should not create a closure process that propagates beyond
the demonstrated local completions.

The implementation is pure, preserves shape, and handles overlapping qualifying
windows consistently when they claim the same color. This is a human work log,
not a token-level model trace.
