# Solve work log

## Exposure statement

Before this blind solve I had not opened the task's generator, canonical rule,
reference solution, private labels, prior notes, or audit evidence. I used only
the visible grids produced by `python3 review.py blind prepare` and local probes
computed from those grids.

## Revision 1 — topology plus reflection symmetry

All three lessons contain one four-cell distractor and four components tied for
the larger/modal area. The changed pair is not consistently congruent: in the
first lesson the two changed masks differ geometrically, and in the second they
also have different perimeters. I therefore rejected an exact-shape-pair rule.

I tabulated two intrinsic properties for each large component:

1. the number of enclosed 4-connected background regions in its tight mask;
2. the number of grid reflection axes (horizontal, vertical, and the two
   diagonals for square masks).

In every visible lesson, exactly one pair has an identical `(holes, axes)`
signature:

- lesson 0: the two changed objects each have one hole and zero axes;
- lesson 1: the two changed objects each have zero holes and one axis;
- lesson 2: the two changed objects each have one hole and one axis.

The remaining candidates differ in at least one of those properties. This also
makes a unique prediction for each masked query: query 0 selects the two
one-hole/one-axis objects, and query 1 selects the two zero-hole/one-axis
objects. The implementation extracts same-color 4-connected components,
selects the modal-area candidates, groups them by this signature, and recolors
the sole group of size two to azure (8). It leaves the grid unchanged rather
than guessing if the signature is not unique.

### Alternatives considered

I also tested exact congruence, minimum shape-edit distance, perimeter equality,
and whether pairs superimpose to fill a rectangle. Each had a visible
counterexample or multiple candidate pairs. The topology/symmetry signature is
the smallest rule I found that is exact on every demonstration and unique on
both queries.

### Remaining uncertainty

The examples support only grid-aligned reflection axes. A task allowing an
oblique symmetry axis would require a more general geometric test, but no
visible component suggests that interpretation.
