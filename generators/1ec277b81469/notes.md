# Working notes: 1ec277b81469

## Base repair

The imported 2.0.1 generator advertised controls that did not determine its
output (`n_distinct_colors`, `palette_size`), exposed degenerate modes that its
own `self_check` rejected, and sometimes ignored requested dimensions.  The
3.0.0 repair keeps only realizable controls and treats explicit values strictly:
shape, active rows, foreground cells, and distinct colors are exact or the call
fails.  Ordinary draws always contain at least two active rows, a multi-cell row,
and a visible move to the right edge.  `RULE_HASH=6ab6552b1d13` binds the pure
Python mirror to the unique canonical Racket rule; all four canonical pairs are
retained exactly.

## Parametric family

The exact canonical program remains the default.  The nearby finite setting
`fill_largest_bbox` first right-packs every row, then selects the unique largest
same-color 4-connected component in that intermediate and fills its bounding
box with color 9.  The selected component is strictly larger than every source
component, and the saved skip-Step-A protected-Racket witness changes the final
output.

Inputs are setting-blind and count-independent.  Two demonstrations and one to
four queries are supported; the four query shapes include 7x11, a tall case,
a wide case, and a substantive 30x30 case.

## Adversarial finding and repair

The first sampler passed the basic candidate bank but a broader semantic sweep
found a real two-demo teaching hole.  Depending on seed, the demonstrations also
fit largest-bounding-box, most-frequent-color, all-cells-of-the-winning-color,
or 8-connected alternatives that changed later query answers.

The repaired sampler alternates two constructive profiles without increasing the
two-demo minimum:

1. `frequency_connectivity` creates a modal checkerboard color that is split
   under 4-connectivity but becomes a larger object under 8-connectivity, plus a
   target-color singleton outside the intended component's box.
2. `rank_geometry` creates a smaller L-shaped component whose bounding box is
   strictly taller, wider, and larger-area than the intended component.

The first profile also leaves a lower distractor row, defeating a bottommost
position shortcut.  Both profiles retain a unique largest 4-connected target
created only after right-packing.

`workspace/parametric/adversarial_probe.py` is the bounded protected-Racket
attack bank.  `semantic_sweep.py` is a cheap many-seed prequalification tool for
future edits; it searches rank, position, frequency, color-extent, connectivity,
partial-intermediate, and whole-component shortcuts.

## Scope

All evidence is finite authoring evidence.  The manifest, preflight, public
projection, and causal witness do not claim owner acceptance or training
admission.
