# Solve work log

## Exposure and visible evidence

Before this solve I had not opened the task's generator, Racket rule, private
labels, reference solution, notes, or audit records. I used only the visible
examples printed by `python3 review.py blind prepare` and the public
`challenge.json` representation.

## Revision 1 — exact-cover tile mosaic

The examples contain exactly nine full 3×3 nonzero tiles scattered on a zero
background. Every tile uses 5 as its base. Eight tiles have one accent color in
a directional motif and one tile is all 5. The motif gives the destination:
corner wedges go to the matching corner, T/side motifs go to the matching edge,
and the all-5 tile goes in the center. The output is the nine source tiles
assembled as a 3×3 mosaic, so it is 9×9.

A simple connected-component split is unsafe because visible query tiles can
touch and an accent color can be reused. I therefore enumerate every full 3×3
window matching one of the nine observed masks, then search for one window per
mask whose 81 cells are disjoint and exactly cover all nonzero input cells. The
selected tiles are copied unchanged into their motif-designated output slots.

Before implementation I ran `/tmp/test_blind_solution.py` against all visible
training pairs and observed the expected `NotImplementedError` from the starter.
Remaining uncertainty is limited to whether hidden instances preserve the same
nine masks and nonzero tile cover; all visible pairs and queries support that
contract.
