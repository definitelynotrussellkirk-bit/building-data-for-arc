# Solve work log

## Prior exposure

Before this solve I had already inspected and repaired the selected generator and had seen its rule authority. This is therefore an exposed post-repair solve, not a blind solve. During the solve itself I used only the visible examples printed by `solve_episode.py prepare` and did not reopen the generator, Racket source, canonical answers, or private query labels.

## Revision 1

**Visible hypothesis.** Every nonzero singleton is a seed. Preserve its color at the center and copy that color to the four orthogonal neighbors (up, down, left, right). Ignore neighbors outside the grid, so edge and corner seeds form clipped pluses. Background remains zero.

**Evidence from visible examples.** Interior seeds become five-cell cardinal pluses. The top-left seed in training example 1 becomes exactly three cells, and the bottom-edge seed becomes four cells, establishing clipping rather than omission. Multiple colors retain their own colors.

**Implementation.** Collect seeds from the original input, create a zero-filled output of the same dimensions, and paint each center plus its in-bounds orthogonal neighbors. Reading all seeds before painting prevents newly painted cells from being mistaken for seeds.

**Alternatives considered.** A 3×3 square, diagonal X, horizontal-only/vertical-only growth, and ignoring boundary seeds all contradict the visible outputs. No revision was needed after the first executable hypothesis.

**Remaining uncertainty.** The visible inputs keep plus neighborhoods separate, so overlap priority is not inferable; the provided instance does not require an overlap policy.
