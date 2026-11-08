# Solve work log

## Prior exposure

I had not opened this task's generator, rule, notes, reference solution, private
labels, or audit evidence before the blind solve. I had only read the packet-level
instructions and the visible examples produced by `blind prepare`.

## Observations and hypotheses

The output is a symmetric `n x n` matrix, where `n` is the number of non-zero
monochrome objects. The diagonal is always blue (`1`). Objects are indexed by
their bounding boxes in reading order (top row, then left column).

I first considered a spatial-adjacency rule because some pairs are nearby, but
that failed on training example 2: the second and third top-row objects are as
close as the first and second, yet only the first pair is linked. Pairwise shape
features explain all four examples instead.

The azure (`8`) pairs are exactly the pairs for which both cropped shapes are
mirror-symmetric top-to-bottom and left-to-right. Examples include a line and a
rectangular frame, a plus and a frame, and two differently sized frames.

The yellow (`4`) pairs are close shape variants after allowing rotations,
reflections, and translation. A useful finite rule for the visible examples is:
the shapes have the same number of enclosed background components and their
minimum cell symmetric difference is at most three. This covers rotated T shapes,
a line versus a T, a T versus a plus, and one-cell frame variants. It also rejects
the close-looking 10/11-cell pair in training example 3 because their enclosed
hole counts differ.

The pairwise precedence used is: diagonal blue; otherwise azure for two fully
mirror-symmetric shapes; otherwise yellow for same-hole shapes within edit
distance three; otherwise black.

## Implementation probe

I wrote a visible-example test harness first. Against the original stub it failed
with `NotImplementedError`, as expected. The implementation extracts color objects,
counts holes by flood fill, enumerates the eight dihedral transforms, computes the
best translated symmetric difference, and builds the pairwise matrix.

## Remaining uncertainty

The threshold of three is inferred from four demonstrations rather than proven as
the hidden rule. The two queries deliberately reuse demonstrated shape families
(line/T/frame and two rotated T shapes), so their decisive pair types are directly
supported even if the broader edit-distance formulation is only an approximation.
