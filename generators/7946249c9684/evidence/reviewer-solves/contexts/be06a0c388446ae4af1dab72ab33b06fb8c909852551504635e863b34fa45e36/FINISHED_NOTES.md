# Solve notes

This is an exposed post-repair solve. I had already studied the task while
repairing its generator, so earlier rule exposure is **yes**. During this solve
I read only `solve/challenge.json` and did not consult the generator, Racket
source, reference solution, or private labels.

## Hypothesis

Treat each column independently. A foreground run is a maximal vertically
contiguous sequence of one nonzero color. Copy only the first and last cell of
each run into an otherwise-zero output. Length-one runs are copied once and
length-two runs remain unchanged. A color change without a zero starts a new
run, which is visible in the second training example.

The three visible examples support the same rule even when foreground cells are
horizontally adjacent or colors repeat elsewhere, so neither connected-component
leaves nor global color extrema is sufficient.
