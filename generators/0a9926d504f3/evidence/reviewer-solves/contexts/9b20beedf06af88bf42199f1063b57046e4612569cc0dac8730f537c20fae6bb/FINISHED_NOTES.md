# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, reference solution,
private query labels, audit records, or any prior explanation. I used only the
visible examples emitted by `blind prepare` and `challenge.json`.

## Revision 1 — colored frame plus red-guided gray cross

**Observation.** Ignoring black, the non-red clues determine four extrema. A clue
on the minimum row supplies the top-edge color, maximum row the bottom-edge
color, minimum column the left-edge color, and maximum column the right-edge
color. A corner clue may supply two edges. Interior duplicates can be decoys:
in train example 2, the second color-6 cell is erased while the extreme color-6
cell supplies the right edge.

**Transformation hypothesis.** Start from a black grid. Paint the left and right
sides between the extrema, then the top and bottom sides so horizontal edges own
the corners. Through the single red (2) clue, paint a gray (5) horizontal and
vertical line across the frame interior. Keep red at the crossing only when it
is strictly interior; a red clue lying on an edge is overwritten by that edge.
Erase all other isolated clues.

**Test-first probe.** I imported the untouched `solution.py` and asserted train
example 0; it failed with the expected `NotImplementedError`. I then implemented
the rule above and planned to check all four visible examples plus the official
visible-only checker. Remaining uncertainty is limited to unseen arrangements
with more than one non-red clue on the same extreme; no visible example is
ambiguous in that way.
