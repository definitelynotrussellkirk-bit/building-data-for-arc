# Fresh solve notes

This is a human work log based only on `solve/challenge.json`. I did not open the generator, Racket rule, reference solution, private labels, or earlier explanation during this solve. I had already seen the task rule during the preceding generator review, so the final declaration must record earlier exposure as **yes**; this is not a blind solve.

## Visible-example analysis

All nonzero cells occur as same-color two-cell dominoes. Comparing each training input with its output:

- A horizontal domino keeps its two original cells and copies its color into the two cells directly below, making a solid 2x2 square.
- A vertical domino keeps its two original cells and copies its color into the two cells directly to the right, also making a solid 2x2 square.
- The operation is independent for every color/object; background cells not in those completion cells remain zero.

Competing hypotheses checked against the visible examples:

1. **Every domino grows downward.** Rejected: vertical color-7 and color-6 dominoes grow right in the visible outputs.
2. **Grow toward the grid center.** Rejected: orientation, not global position, consistently determines the side.
3. **Replace each domino rather than preserve it.** Rejected: original cells remain present in every output.
4. **Use color-specific directions.** Rejected: different colors obey the same orientation mapping.

## Planned implementation

Find 4-connected same-color components in the original grid. For each two-cell straight component, classify it as horizontal or vertical. Copy the input, then paint the missing half of its 2x2 square: one row below a horizontal component or one column right of a vertical component. Components are detected before editing so newly painted cells cannot be mistaken for new inputs.

## Revision 1

Implemented the component-based transformation in `solution.py`. This avoids scan-order feedback and directly mirrors the visible object-level relation.
