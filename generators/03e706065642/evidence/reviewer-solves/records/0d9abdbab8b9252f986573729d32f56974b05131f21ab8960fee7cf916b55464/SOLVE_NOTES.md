# Solve work log

I had earlier exposure to the task rule while repairing the assigned generator, so this
is an exposed fresh solve rather than a blind solve.  During this episode I consulted
only the visible examples and the generated solve files; I did not reopen the generator,
Racket source, reference solutions, private labels, or earlier solution explanations.

## Revision 1

The outputs are 3×3 symmetric matrices with 2 on the diagonal.  Across the examples,
off-diagonal 2s group framed motifs by a property that ignores motif color and exact
pixel count.  The visible motifs suggest the property is the pair of reflection flags:
left/right symmetry and up/down symmetry of the motif's tight binary crop.  For example,
train 0 groups the first two motifs despite different exact shapes, while train 3 puts
all three in distinct groups.

Implementation plan: identify each disconnected color-1 rectangular frame; sort frames
left-to-right; crop each non-background, non-frame motif tightly; compute equality with
its left/right and up/down flips; output 2 where two two-flag signatures match, else 0.
This avoids relying on frame size, spacing, motif color, or exact shape.

Remaining uncertainty before checking: color-1 frame components could theoretically
connect, but every visible example separates them by at least one zero column, and all
motifs are nonempty.
