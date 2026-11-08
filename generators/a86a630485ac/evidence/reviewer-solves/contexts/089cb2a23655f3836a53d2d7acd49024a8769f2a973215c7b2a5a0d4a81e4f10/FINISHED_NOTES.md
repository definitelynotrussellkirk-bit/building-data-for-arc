# Solve work log

## Exposure declaration before solving

This is the required post-repair solve. I had already inspected and edited the
assigned generator and had therefore been exposed to the intended rule before
this episode. During the episode itself I did not reopen the generator, Racket
source, canonical answer data, reference solutions, private labels, or previous
solution explanations. I used only `solve/challenge.json` and my own analysis.

## Revision 1 — retain objects symmetric across their vertical centerline

**Observation.** Each input contains several separately colored connected
objects. The output preserves the plus-shaped color-7 object in training pair 1,
the color-7 object in pair 2, and the color-4 object in pair 3. In each case,
reflecting occupied cells left-to-right inside that object's own bounding box
leaves the shape unchanged. The erased objects fail that test, including shapes
that are symmetric top-to-bottom instead.

**Hypothesis.** Treat each nonzero monochromatic 4-connected component as an
object. Reflect each occupied cell's column about the midpoint of that object's
minimum and maximum columns. Copy the object to an initially blank output if and
only if every reflected cell is occupied.

**Implementation choice.** Components are discovered independently rather than
pooling all cells of one color, because the visible transformation is object
based. Reflection uses absolute component coordinates (`min_c + max_c - c`),
which is equivalent to normalizing the object to its bounding box.

**Alternatives rejected.** Keeping top-bottom-symmetric objects is contradicted
by the erased horizontal-T-like objects. Keeping largest, widest, or most common
shapes is contradicted within the visible pairs by kept and erased objects with
similar sizes and extents.

**Remaining uncertainty.** The visible examples use one color per object, so
they do not directly test two disconnected components of the same color. The
component-wise implementation is the least committal object interpretation.
