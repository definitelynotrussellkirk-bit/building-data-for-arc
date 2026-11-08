# Solve work log

## Exposure declaration before solving

I had not opened the task's generator, Racket rule, reference solution, private
query labels, prior solve notes, or audit evidence. I used only the visible
examples prepared in this directory and local Python checks against their public
training outputs.

## Revision 1 — crop the payload and apply the corner-coded symmetry

**Observation.** Every input has one isolated nonzero instruction cell at
zero-based coordinate `(0, 0)` and a separate compact multicolor payload. The
output contains the payload's colors but not the isolated instruction cell, and
is exactly the payload's nonzero bounding-box crop after a symmetry operation.
Internal zero cells remain part of the crop.

**Visible probes.** After excluding only `(0, 0)`:

- Training 0 has instruction color `1`. Its 3×3 payload becomes the shown output
  under a 90-degree clockwise rotation.
- Training 1 has instruction color `2`. Its 3×3 payload becomes the shown output
  under a 180-degree rotation.
- Training 2 has instruction color `3`. Its 3×3 payload becomes the shown output
  under a left-right reflection.

The color `3` also occurs inside training payload 2, so the implementation must
remove the instruction by coordinate, not delete every occurrence of its color.
The second query's payload is rectangular (3×4), so the crop and transforms are
implemented for arbitrary rectangular blocks rather than assuming 3×3.

**Implementation.** Find the bounding box of all nonzero cells except `(0, 0)`,
copy that full rectangle, and dispatch on the corner color: `1` → clockwise
quarter-turn, `2` → half-turn, `3` → left-right reflection. For an unseen code,
return the crop unchanged rather than inventing an unsupported mapping.

**Remaining uncertainty.** The visible examples define only instruction colors
1–3, and each appears once. The two query instructions are 1 and 2, whose mappings
are directly demonstrated. I cannot infer a broader codebook for other colors
from these examples.
