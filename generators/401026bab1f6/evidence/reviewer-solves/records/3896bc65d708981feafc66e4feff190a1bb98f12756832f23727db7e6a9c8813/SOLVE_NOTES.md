# Blind solve: 401026bab1f6

## Exposure and observations

I opened only the public preparation output and `challenge.json`. I have not
opened this task's generator, rule, notes, solutions, audits, or private labels,
nor the repair generator. An independent agent was given only the same visible
challenge for a reasoning cross-check; it received no proposed rule from me.

Visible example shapes are 10x10 -> 10x10, 11x12 -> 11x12,
12x11 -> 12x11, and 12x12 -> 12x12. Query inputs are 16x18 and
17x17; their output dimensions and answers are hidden.

## Hypothesis and probe

Each blue (1) connected component is a rectangular frame. Reflect each yellow
(4) interior cell vertically within its own frame, preserving its column.
Paint orange (7) at the reflected location only when that location was empty.
Keep all original cells. This explains why example 3 adds only five cells from
nine yellow cells: reflections that land on yellow stay yellow.

I enumerated the actual changed cells in all four visible pairs. In example 0
the frame's top/bottom rows sum to 10: yellow row 3 reflects to row 7 and row 4
to row 6. In example 1 each bottom interior row reflects to the top interior
row, separately in the two frames. Example 2 distinguishes vertical reflection
from simple horizontal reflection. Example 3 covers overlaps and center rows.

## Revision 1

Implemented a four-neighbor search for blue frames and the inferred reflection.
No speculative unsuccessful revision was submitted. Colors 1, 4 and 7 are fixed
because every visible example uses those semantic roles; other palettes remain
unobserved. The implementation assumes separate axis-aligned blue frames, as in
the visible inputs. I will use the official visible-only checker and stop if
all visible examples match and query execution succeeds. Hidden correctness is
not known and will not be claimed.
