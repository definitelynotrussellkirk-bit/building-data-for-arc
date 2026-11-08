# Solve work log

## Prior exposure

Before this blind episode I had not opened task `ba090ac77d54`'s generator,
Racket rule, notes, solutions, audits, or private labels. I had only read the
packet-level instructions and the generated `challenge.json`.

## Revision 1 — Manhattan Voronoi fill

**Observation.** Each input has a color-5 rectangular frame, a color-0 interior,
and a few colored singleton sites. In the first training pair, vertically aligned
sites produce horizontal constant-color bands, with color 8 exactly on rows tied
between adjacent sites. In the second pair, horizontally aligned sites produce
the analogous vertical bands. The oblique boundaries in pairs three and four
look like 45-degree Manhattan-distance bisectors.

**Hypothesis.** Fill every interior cell with the color of its uniquely nearest
colored site under Manhattan distance. Put color 8 wherever the minimum distance
is shared by sites of different colors. Preserve the frame.

**Probe.** A local Python comparison against all four visible outputs found zero
cell mismatches for Manhattan distance, versus 30 for squared Euclidean distance
and 91 for Chebyshev distance. This probe used only `challenge.json`.

**Implementation choice.** Infer the frame color from the top-left corner, treat
0 as the interior background, collect all other interior cells as sites, and use
the set of nearest colors so coincident/equidistant sites of the same color do not
create an artificial color-8 boundary.

**Remaining uncertainty.** The visible examples use distinct site colors and a
color-5 frame, so same-color duplicate sites and malformed/nonrectangular frames
are not directly tested. The implementation handles same-color ties naturally and
preserves the supplied border rather than repainting it.
