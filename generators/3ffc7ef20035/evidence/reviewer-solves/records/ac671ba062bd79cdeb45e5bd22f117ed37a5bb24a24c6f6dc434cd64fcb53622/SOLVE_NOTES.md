# Solve notes

This human-readable work log uses only the newly prepared visible examples. I
had earlier exposure to the task rule during generator work, so this is not an
independent blind discovery. During this solve I did not consult generator
source, Racket/reference code, private labels, or the prior solve episode.

In all three demonstrations, color 1 is the transformed object. The output
replaces every cell in the inclusive axis-aligned bounding rectangle spanning
all color-1 cells with color 8. This fills zero-valued gaps in diagonal and
stair-like objects. The separate nonzero object (colors 5, 9, or 7 here) remains
unchanged.

The implementation copies the input, computes the row and column extrema of all
blue cells, fills that rectangle with 8, and preserves everything else. It
returns an unchanged copy if no blue cells exist, though the visible lesson does
not require that case.
