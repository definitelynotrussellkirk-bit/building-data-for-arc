# Solve work log

## Exposure statement

Before this blind solve I had read only the packet-level instructions and the
visible examples printed by `solve_episode.py blind prepare`. I did not open the
assigned repair generator, either task's Racket rule, private labels, reference
solutions, or prior solve explanations.

## Revision 1 — bounding-box-relative mark transfer

**Observation.** Every input is three equal-height panels separated by full-height
color-5 columns. The first and middle panels contain the same base object. The
middle panel has extra color-8 cells. The third panel contains a differently
colored target object, and the output is the third panel with those extra cells
transferred.

**Probe across the four demonstrations.** I compared the top-left corner of the
nonzero bounding box in panel 1 with that in panel 3. Translating the panel-2
additions by that offset predicts every output exactly:

- example 0: offset `(0, -1)`;
- example 1: offset `(-2, 0)`, including an 8 overwriting the target center;
- example 2: offset `(5, 0)`;
- example 3: offset `(-1, -2)`, again allowing overlap.

This rejected weaker alternatives such as centroid alignment, copying the marks
at absolute coordinates, or aligning object centers. Different source/target
shapes make top-left bounding-box anchoring the consistent rule.

**Implementation.** Split on full-height 5 columns, copy panel 3, find the source
and target nonzero bounding-box top-left cells, then overlay every nonzero cell
that differs between panels 1 and 2 after applying the offset. Out-of-bounds marks
are ignored defensively, though the visible lessons keep them in bounds.

**Remaining uncertainty.** The examples use color 8 for every added mark. The
code intentionally transfers any nonzero addition/change rather than hard-code
8, because the relational rule is clearer and preserves the shown behavior.
