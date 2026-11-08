# Parametric family for `14dacb3b518f`

This adapter exposes a finite two-rule family over the same setting-independent
input grammar.

- `hole_presence` is the exact accepted canonical program: any object with at
  least one enclosed background region becomes 8; every other object becomes 2.
- `most_holed_size_threshold` first identifies the unique two-hole object,
  reads its occupied-cell count, then recolors every object 8 iff its size is at
  least that threshold.  This is a genuine input-dependent A→intermediate→B
  rule, not a fixed constant disguised as composition.

Every generated scene has exactly five separated color-6 components with hole
counts `[0, 0, 0, 1, 2]`: a unique two-hole anchor, a one-hole object, a large
solid, a small solid, and a leaky bbox-gap distractor.  The one-hole and leaky
objects alternate above and below the anchor-size threshold, so visible examples
reject fixed size-rank and bbox-gap shortcuts.  The required 2–6 demonstrations
provide varied placements, dimensions, and threshold ranks. Inputs do not depend
on the selected setting or requested total count. Query four is a substantive
30×30 boundary-contact stress case.
