# Solve work log

## Exposure declaration

I had already inspected the canonical rule and generator while repairing this assigned task, so this is an exposed post-repair solve, not a blind solve. During this solve episode I read only `solve/challenge.json`, `solve/README.md`, the provided stub, and this work log; I did not reopen the Racket rule, generator, reference solutions, or private labels.

## Revision 1

### Visible-example observations

- Every changed cell was originally `0` and became `4`.
- Each changed cell had a `7` immediately above and a `7` immediately below in the same column.
- The endpoints stayed `7`.
- All qualifying locations changed, including two adjacent targets that share a `7` endpoint in the third training example.
- Horizontal arrangements were not implicated.
- An occupied center stayed occupied: in the first training example, `7,2,7` and `5,0,5` controls did not become `4`.
- A wider vertical span was not enough; the flanking `7`s had to be immediate neighbors of the zero.

### Hypothesis

Copy the input. For every interior row and every column, replace the cell with `4` iff the original cell is `0` and its immediate vertical neighbors in the original input are both `7`. Leave everything else unchanged. Reading from the original input avoids newly written `4`s affecting later decisions.

### Implementation and uncertainty

Implemented the direct local scan in `solution.py`. The three visible examples make orientation, color, midpoint emptiness, adjacency, exhaustive application, and shared endpoints explicit. Remaining uncertainty is only masked-query scoring, which the solve harness intentionally withholds.
