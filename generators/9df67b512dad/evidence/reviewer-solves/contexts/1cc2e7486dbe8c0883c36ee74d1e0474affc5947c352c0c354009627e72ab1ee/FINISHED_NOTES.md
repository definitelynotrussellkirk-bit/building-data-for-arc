# Solve work log

I had no earlier exposure to task `9df67b512dad`, its generator, or its rule. I
used only `solve-blind/challenge.json` and small local summaries of the visible
examples.

## Revision 1 — border/interior overwrite compression

Each input naturally splits into three row bands (first row, all interior rows,
last row) and three analogous column bands.  For every visible example, the
output cell is the last nonzero color encountered in ordinary row-major order
inside the corresponding band; an empty band yields 0.

The decisive cases were ties.  In training example 3, the middle-right band
contains `[9, 7]` and the target is 7.  In training example 2, the top-middle
band contains `[5, 9]` and the target is 9.  Thus plain majority voting is not
enough, while ordered overwrite explains both.  Other populated bands contain
sequences such as `[1, 8, 8, 8]` and `[9, 7, 7, 7]`, also ending in the visible
target color.

I implemented that direct rule.  Remaining uncertainty is only whether the
reference describes the operation as overwrite/compositing rather than “last
nonzero”; those are operationally equivalent on the visible examples.
