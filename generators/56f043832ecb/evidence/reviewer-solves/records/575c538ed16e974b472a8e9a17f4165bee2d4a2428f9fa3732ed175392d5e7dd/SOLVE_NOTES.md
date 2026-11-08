# Solve work log

## Exposure declaration before solving

I had not opened task `56f043832ecb`'s generator, Racket rule, notes, prior
solutions, audit records, or private labels. I used only the visible examples in
`challenge.json` and the generated solve scaffolding.

## Revision 1 — fill enclosed background components

**Observation.** In each training pair, zero cells completely enclosed by a
single nonzero color become that color. The left color-3 rectangle in training
example 2 is filled, while the color-7 shape is not because a gap connects its
interior to the outside. In training example 3, the extra color-9 pixel below the
rectangle is preserved while the truly enclosed interior is filled.

**Hypothesis.** The transformation is topological rather than specifically
"fill every bounding box": find each 4-connected zero component; if it does not
touch a grid edge and all of its nonzero orthogonal neighbors have one color,
fill the component with that color. Leave the exterior and open shapes alone.

**Implementation.** Breadth-first search over zero components, recording edge
contact and boundary colors. This also handles multiple independent enclosures
and an enclosure with harmless attached exterior pixels.

**Alternatives considered.** Filling every nonzero component's bounding box
would accidentally fill the open color-7/6 shapes. Detecting only perfect
rectangular borders is narrower than the visible evidence and unnecessary.

**Remaining uncertainty.** The visible examples do not show a hole whose
boundary contains multiple colors. The implementation conservatively leaves
such a region unchanged rather than guessing a fill color.
