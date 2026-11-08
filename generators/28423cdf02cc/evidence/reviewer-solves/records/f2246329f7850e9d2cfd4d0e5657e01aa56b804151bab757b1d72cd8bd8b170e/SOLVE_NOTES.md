# Post-repair visible-only solve: 28423cdf02cc

## Exposure declaration

Earlier rule exposure: yes. Before this episode I repaired this generator and
read its canonical rule. This is therefore an exposed solve, not a blind solve.
During the solve I used only the newly prepared public examples and my own
Python; I did not reopen the generator, Racket rule, reference explanations or
private query labels. Preparation and checking execute the reference internally.

## Visible evidence and hypothesis

The first two examples each have 9-row by 13-column inputs and outputs. The third
has a 13-row by 13-column input and output. Each source has a colored 3x3 tile in
the top-left corner, a gray vertical divider, and blue point markers on the right.
The outputs preserve the tile/divider and replace each blue point with a full copy
of the tile centered on that point, preserving its original orientation.

Example 2 includes centers such as (1,9), (5,9), (8,11), and (11,11), so a fixed
3-spaced stamping lattice does not explain the visible behavior. A centered stamp
at every blue marker does. I retain original cells and write copies only onto
background or blue cells; the demonstrations contain no conflicting overlap.

## Revision 1

Implemented direct marker detection and centered copying from the original 3x3
template. The result starts as a fresh copy of the input. The two queries have
10x17 and 10x18 inputs; their output shapes and correctness remain withheld.
No artificial wrong attempt or teaching negative was created.
