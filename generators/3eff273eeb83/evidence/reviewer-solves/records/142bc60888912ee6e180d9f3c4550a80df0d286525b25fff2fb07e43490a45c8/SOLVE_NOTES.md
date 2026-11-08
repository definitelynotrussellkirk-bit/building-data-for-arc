# Solve work log

This is a human-authored visible-example work log. I had already seen the task's
rule during the required generator review, so this is **not blind**; I did not
consult the Racket source, generator implementation, reference solutions, or
private query labels during this solve phase.

## Revision 1 — visible geometry hypothesis

Across all three demonstrations, color 5 is a fixed pivot and the input color-2
cells form a straight one-sided line from it. The output preserves the pivot,
recolors every original 2 to 3, and places the same number of 2 cells at the
same pivot-relative distances after a 90-degree clockwise turn:

- a line left of the pivot turns upward;
- a line right of the pivot turns downward;
- a line above the pivot turns rightward.

The coordinate map for an input offset `(dr, dc)` is therefore `(dc, -dr)`.
I wrote a shape-preserving solver that applies this map to every color-2 cell.
The main competing visible rule was a counterclockwise turn, but each training
example places the copied line on the opposite side from that rival. Another
possible shortcut was copying at most three cells; the first two demonstrations
contain four cells and visibly require all four, so the implementation preserves
all source distances.

Probe: `python3 -m pytest -q solve/test_visible.py`. The initial template failed
with `NotImplementedError`; after implementing the coordinate map, all visible
training examples passed. I then used the packet's visible-only check command.
Remaining uncertainty is limited to the masked query labels, which are
intentionally withheld; both query inputs follow the demonstrated grammar.
