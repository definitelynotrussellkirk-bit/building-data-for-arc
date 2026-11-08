# Solve work log

I had not opened task `c1b80aa665e4`'s generator, rule, notes, solutions, audit
records, or private labels before this solve. I had only read the packet-level
instructions and the visible `solve-blind/challenge.json`.

## Revision 1 — singleton same-color components

**Hypothesis.** Treat each nonzero color as a set of orthogonally connected
components. Recolor a component to `9` exactly when its size is one; leave every
larger component and all background cells unchanged.

**Evidence from the visible examples.** In example 1, isolated colors `2` and
`5` become `9`, while the two-cell vertical `4` object remains. In example 2,
the isolated first and last `3` cells become `9`, while the adjacent vertical
pair of `3`s remains. In example 3, isolated `3`, `4`, and `6` cells become `9`,
while the three-cell vertical `2` object and two-cell horizontal `8` object
remain. This also distinguishes object size from color frequency: example 2
contains three cells of the same color, but only the disconnected singleton
components change.

**Implementation.** Scan the grid, flood-fill each orthogonally connected
same-color nonzero component, and recolor only components of length one. The
implementation copies the grid instead of mutating the input.

**Probe.** Before implementation, a visible-example test failed on the provided
`NotImplementedError`. After implementation, the same test passed all three
visible pairs. No alternative rule was needed. The main remaining uncertainty is
whether diagonal adjacency should join components, but the examples explicitly
support ordinary orthogonal ARC object connectivity and provide no diagonal-only
counterexample.
