# Solve work log

## Exposure declaration

Before solving I had read only the packet-level instructions and the visible assignment text. I did not open this task's generator, Racket rule, canonical/private labels, prior solution notes, or reference solution.

## Revision 1 — colored marker becomes a same-colored outer frame

Across all three demonstrations, the input contains a zero background and exactly one nonzero cell. The output preserves the input dimensions, removes the interior marker, and colors every cell on the outer perimeter with that one nonzero color. Marker position varies (center, off-center, near the top), while the output depends only on its color, so position appears deliberately irrelevant.

Implemented `solve(grid)` to identify the sole nonzero color, create an all-zero grid of the same shape, and color rows 0 and H-1 plus columns 0 and W-1. Added explicit handling for an empty grid and rejection of ambiguous multi-color inputs. The two hidden queries should therefore become 4- and 8-colored rectangular frames respectively.

Remaining uncertainty: visible examples do not show multiple nonzero cells, multiple nonzero colors, a marker on the border, or one-cell-wide dimensions. The selected implementation follows the simplest rule supported by every visible example rather than guessing behavior outside that demonstrated domain.
