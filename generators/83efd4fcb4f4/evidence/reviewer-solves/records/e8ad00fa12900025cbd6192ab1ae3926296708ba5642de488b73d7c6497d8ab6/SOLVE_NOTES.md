# Solve work log

I had no earlier exposure to task `83efd4fcb4f4`, its generator, its rule, its
private labels, or any prior explanation before this solve. I used only the
visible examples printed by `python3 review.py blind prepare`.

## Revision 1 — orthogonal-cross centers

**Hypothesis.** The transformation preserves every input cell except a zero at
the center of an orthogonal cross whose north, south, west, and east neighbors
are all color 3. Each such center becomes color 8. Other colors (including 6
and 7) appear to be distractor structures and remain unchanged.

**Visible checks.** In train example 0, the two added 8s are at `(1, 3)` and
`(7, 2)`, and both have four orthogonal 3-neighbors. Train examples 1–4 show
the same condition for every added 8. Diagonal neighbors are irrelevant, and
no border cell can qualify because it lacks four orthogonal neighbors.

**Implementation.** Copy the grid, scan only interior zero cells, test the four
neighbors in the original grid, and write 8 into the copy. Reading from the
original prevents one newly written 8 from affecting another candidate.

**Alternatives considered.** The 6/7 shapes might select a subset or direction,
but all visible added cells are explained exactly by the local cross predicate,
including crosses far from those colors. I found no visible counterexample.

**Remaining uncertainty.** The masked queries are unavailable; the local rule
is fully consistent with all five visible training pairs.
