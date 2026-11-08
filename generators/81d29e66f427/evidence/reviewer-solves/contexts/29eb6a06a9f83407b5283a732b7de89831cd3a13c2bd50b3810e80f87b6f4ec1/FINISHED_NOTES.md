# Solve work log

## Exposure declaration before solving

I had already read the selected task's generator and Racket authority while doing the assigned repair, so this is an exposed post-repair solve, not a blind solve. During this solve I consulted only `solve/challenge.json`, this work log, my own Python implementation, and the visible-only checker. I did not reopen the generator, Racket rule, canonical ledger, private labels, or earlier solution explanations.

## Revision 1 — Boolean gallery hypothesis

Visible observations:

- Every input has nonzero color keys on row 0 and two hollow color-5 rectangles below it.
- The output height equals a frame's interior height. Its width is one interior-width panel per top-row key, with a blank column between panels.
- The left frame's color-2 cells and the right frame's color-3 cells occupy corresponding coordinates.
- Comparing visible outputs against the aligned masks: key 2 keeps cells occupied by either mask (union); key 3 keeps only overlap (intersection); keys 4 and 6 keep cells occupied by exactly one mask (exclusive-or). Panels follow the left-to-right order of nonzero keys, not sorted numeric order.

Implementation plan: find exact hollow color-5 connected components, extract the two interior coordinate sets, apply the operation chosen by each key, recolor selected cells to 8, and gallery the panels with one zero column between them. This also handles the test's noncanonical XOR key 6 rather than hard-coding key 4.

Remaining uncertainty before checking: none in the visible examples; the main risk is frame parsing or panel placement, so the implementation validates frames geometrically rather than relying on fixed columns.
