# Solve work log

## Exposure declaration before solving

Before this solve I read only the packet-level `WELCOME.md`, `RETURN-GUIDE.md`,
`repo/AGENTS.md`, the assignment text, and `solve-blind/challenge.json`. I did
not open task `3194379886a5`'s generator, Racket rule, notes, prior solves,
private labels, or review records. I had no earlier exposure to this task's rule.

## Revision 1 — rotational duplicate selected by the odd color

The inputs are horizontal collections of same-sized panels separated by full
height gray (`5`) columns. In every training example, three panels use one
object color and one panel uses a different marker color. Exactly one of the
three common-color objects has the same cropped binary shape as the marker
object after a rotation:

- training 1: the third object becomes the marker object after 180 degrees;
- training 2: the second object becomes it after a quarter-turn;
- training 3: the second object likewise has the marker object's rotated shape.

The output preserves the matching common-color panel's original canvas position
and recolors its occupied cells with the marker color. I checked all four
rotations on the two test inputs using a small Python probe derived only from
`challenge.json`: test 1 selects panel 2 (zero-based index 1), and test 2 selects
panel 3 (zero-based index 2). The implementation therefore splits the panels,
identifies the uniquely occurring object color, trims binary object masks for
shape comparison, checks four rotations, and recolors the matching panel.

Remaining uncertainty: the visible examples establish rotation but not mirror
reflection, so the program intentionally does not treat reflections as matches.

## Revision 2 — final panel is the marker

Revision 1 failed at execution on the visible examples. The implementation had
mistakenly identified the marker by a uniquely occurring color. Re-reading the
first visible training input showed the counterexample: its four object colors
are all different (`1`, `4`, `3`, `8`), while the marker is still structurally
the final panel. The stable positional relation across all three examples is:
use the last panel as the rotated-shape query, search only the preceding panels,
and recolor the matching preceding panel with the last panel's object color.
I changed only marker selection from color-frequency inference to final-panel
selection; the rotation, placement, and recoloring logic remains unchanged.

## Revision 3 — include reflection as well as rotation

Revision 2 still failed. A direct binary comparison of the third visible
training case showed that its selected second panel is *not* rotation-equivalent
to the final panel. It becomes the final panel after a reflection combined with
a rotation (equivalently, another member of the square's dihedral symmetries).
The first two examples happen to need rotations only, so my earlier probe was
incomplete. I broadened shape equivalence to the eight rotations/reflections of
the cropped mask. Panel order, output placement, and marker-color transfer are
unchanged. This also preserves a unique match in both visible test inputs.
