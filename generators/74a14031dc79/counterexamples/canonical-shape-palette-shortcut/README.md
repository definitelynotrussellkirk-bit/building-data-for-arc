# Canonical shape-and-palette shortcut counterexample

The shortcut applies the correct aligned occupancy-OR only when the input is
`3×7` with left/right/separator role colors `(6,8,4)`; otherwise it emits an
all-zero output. It fits all six canonical train/test pairs because every one
has exactly that shape and role palette.

This retained input is an ordinary, no-override production sample
(`seed=20261007`, `sample_index=1`, `difficulty=easy`). It is still `3×7`, but
uses role colors `(5,3,1)`. The canonical Racket rule emits six blue cells,
while the shortcut emits all zeros. See `provenance.json`, `racket_output.json`,
and `rival_output.json`; the full source-bound apply receipt is retained at
`WORK/checks/shortcut-74a14031dc79/racket.json`.

The repaired four-slot curriculum emits noncanonical role palettes in every
nonzero slot and off-canonical heights in slots 2 and 3. Task-local regressions
verify that every sliding three-demonstration lesson refutes this shortcut.
