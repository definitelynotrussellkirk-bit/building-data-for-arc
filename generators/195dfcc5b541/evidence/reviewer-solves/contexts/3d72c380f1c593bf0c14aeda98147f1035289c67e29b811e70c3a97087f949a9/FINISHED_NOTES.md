# Solve work log

This is a human-readable work log, not a captured model trace. I had already
seen and analyzed the task rule while repairing its generator, so this is an
**exposed post-repair solve**. During this solve I did not reopen the generator,
Racket rule, reference implementation, private labels, or earlier solution
notes. I used only the visible episode printed by `solve_episode.py prepare` and
the visible-only checker.

## Revision 1

**Visible observations.** Each input contains one compact four- or five-cell
shape in color 8. The output preserves that object and changes selected color-3
cells to 8. The changed 3-cells form several copies of the color-8 shape. Across
the three examples, both rotations and mirror images appear necessary; isolated
3-noise remains unchanged. Grid dimensions and all nonmatching colors remain
unchanged.

**Hypothesis.** Treat all input color-8 cells as a normalized stencil. Enumerate
its eight dihedral orientations (four rotations, with and without reflection).
At every legal translation, if every stencil cell is color 3, recolor those
cells to 8. Do not require the bounding box around a match to be empty, because
the examples support matching the marked cells themselves amid dense unrelated
background.

**Implementation/probe.** `solution.py` normalizes the stencil, deduplicates its
dihedral variants, finds every all-3 placement in the original input, and
recolors the union of matched cells in a copied grid. The next step is the
visible-only `solve_episode.py check`; no query labels are consulted.

**Remaining uncertainty before the check.** If arbitrary 3-noise accidentally
forms overlapping copies, the intended rule may impose an ordering or
non-overlap convention. The visible examples appear constructed with separated
matches, so the union-of-matches interpretation is the simplest supported rule.

**Visible-only check result.** Revision 1 executed successfully and matched all
3 of 3 visible training outputs. I made no further code revision because the
hypothesis explains every observed change and the checker exposed no contrary
visible evidence. Masked-query correctness was not shown.
