# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, canonical record, reference solution,
private labels, prior solution explanations, or audit evidence for task
`cc100a8ad437`. I used only the visible grids produced by `blind prepare`,
`solve-blind/challenge.json`, and my own coordinate probes.

## Revision 1 — orientation-specific stencil matching

**Observation.** Every input has a full-height nonzero separator column. The
foreground object to its left is a stencil. The output has the separator and the
entire left panel removed, preserves the right panel's height, and starts from an
all-zero canvas.

**Hypothesis.** Search the right panel for translations of the left stencil in
its original orientation. A translation is a match when every occupied stencil
cell has the stencil's color; unrelated foreground cells, including cells inside
the stencil bounding box, are allowed as clutter. For each match, fill the
stencil's complete bounding rectangle with color 8.

**Probe.** A Python coordinate scan derived the left stencil mask and enumerated
all translations whose required cells have the stencil color. The match starts
were:

- train 0: `(3, 11)`, `(7, 6)`
- train 1: `(0, 9)`, `(4, 8)`
- train 2: `(2, 10)`, `(3, 7)`
- train 3: `(1, 11)`, `(7, 10)`

These starts reproduce exactly the two 8-rectangles in each visible output.
The same scan predicts test starts `(4, 6)`, `(5, 10)` and `(1, 7)`, `(5, 4)`,
`(8, 14)` respectively.

**Alternatives rejected from visible evidence.** Rotation/reflection invariance
is inconsistent with train 0, where a rotated tetromino is not marked. Matching
whole connected components is inconsistent with trains 1 and 3, where valid
stencils are embedded in larger clutter. Requiring the bounding-box zeros to
remain zero is also inconsistent with those examples.

**Remaining uncertainty.** The examples contain one reference color on the left,
so the implementation chooses its most frequent nonzero color. The visible task
does not establish behavior for multiple independent left-hand stencils.
