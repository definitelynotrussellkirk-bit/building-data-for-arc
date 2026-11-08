# Solve work log

This is a human work log from the visible examples. I had earlier exposure to the
family and its rule while reviewing the generator, so this is intentionally an
**exposed** post-repair solve, not a blind solve. During this solve I did not open
the generator, Racket source, reference solution, private labels, or previous
solve explanations.

## Revision 1

The visible examples show exactly one pair of opposite solid colored borders and
several color-1 markers. Each marker causes one new cell beside it on the line
toward one of those borders. Markers in the first half of the perpendicular axis
project toward the top or left border and use that border's color; markers in the
second half project toward the bottom or right border and use its color. The
marker itself remains unchanged.

The 13-column vertical example resolves the odd-axis tie: a marker at column 6
projects left, so the exact middle index belongs to the first/top-left half. I
implemented this as `2 * axis < extent`; otherwise the marker belongs to the
second/bottom-right half. Orientation is inferred by finding which opposite
border pair is solid. The transformation scans marker coordinates from the
original input and writes into a copy, preventing newly painted cells from being
mistaken for markers.

Remaining uncertainty before checking: none on the displayed domain; malformed
inputs with zero or two solid border pairs are rejected explicitly.
