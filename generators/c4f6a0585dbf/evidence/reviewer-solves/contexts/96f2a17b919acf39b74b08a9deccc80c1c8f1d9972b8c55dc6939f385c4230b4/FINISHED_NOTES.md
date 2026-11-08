# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private labels,
or prior explanation before this blind solve. I had only read the packet workflow and
assignment metadata.

## Revision 1 — translated/rotated template matching

**Observation.** Every input contains one solid blue rectangle whose interior yellow
cells define a small point pattern. Outputs preserve the input and turn zeros into blue
inside other rectangles with the same dimensions/orientation as the template. The
new rectangles surround matching yellow constellations. The first demonstration uses
both horizontal and vertical copies of a two-point pattern; the later demonstrations
also show rotated copies.

**Boundary observation.** Some highlighted rectangles are clipped by the lower grid
edge. In those cases two template markers remain visible while another expected marker
would lie outside the grid. A one-marker clipped hypothesis overgenerates many boxes,
whereas requiring at least two visible markers reproduces all demonstrations.

**Probe.** I enumerated every translation of every distinct rotation/reflection of the
template marker mask. A candidate must have at least two in-grid expected markers, all
of them yellow, and no additional yellow cell anywhere in the visible part of its
rectangle. Painting the zero cells of all such candidates reproduces all three visible
training outputs exactly, including overlapping and clipped boxes.

**Alternatives rejected.** Requiring every marker to be in bounds misses the clipped
examples. Accepting one visible marker paints many false boxes. Matching only the
marker bounding box cannot explain the one-cell blue margins or the non-square rotated
example.

**Remaining uncertainty.** The demonstrations do not distinguish rotations-only from
all reflections for every possible asymmetric mask. I use the full dihedral set because
the visual instruction is shape matching without an orientation cue, while duplicate
orientations are removed. Matching always uses the original input, so newly painted
blue cells cannot create more candidates.
