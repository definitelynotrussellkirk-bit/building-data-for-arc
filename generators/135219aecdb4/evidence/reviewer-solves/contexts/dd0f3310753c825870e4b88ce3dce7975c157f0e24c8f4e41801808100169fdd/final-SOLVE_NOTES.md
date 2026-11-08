# Solve notes — 135219aecdb4

## Exposure declaration

I had already inspected the task's generator and rule authorities during the required generator-review phase. I did not reopen or consult them after `solve_episode.py prepare`; this solve was based only on `solve/challenge.json` plus my own probes. Accordingly this is **not** claimed as a blind first exposure.

## Visible-example observations

- Every nonzero cell is preserved.
- Outputs use the colors 1–4 and are consistent with a 4×4 Latin-square constraint: no repeated nonzero value in a completed row or column.
- A zero is safely fillable when exactly one color from 1–4 is absent from the union of its row and column.
- Some fills unlock later fills, so a single simultaneous sweep is insufficient.

## Hypotheses considered

1. **Copy a fixed Latin-square template.** Rejected: the three training outputs use different row arrangements, so position alone is not enough.
2. **Complete any row or column with one zero.** This explains many visible cells, but it is too weak for the second test input: after obvious single-hole fills, two coupled pairs remain.
3. **Choose the singleton row/column candidate intersection, synchronously and repeatedly.** This explains every training pair and resolves the coupled second test in three rounds without guessing.
4. **Run in-place until stable.** Rejected as the primary formulation because update order would become an unobserved extra rule. Synchronous snapshots are deterministic and match the staged chains.

## Probe on the interlocked test input

For the second test grid:

- Round 1 forces the first cell of row 3 to `1` from its column and the last cell of row 1 to `3` from its column.
- Round 2 jointly forces row 1 column 2 to `4` and row 3 column 3 to `4` even though neither row nor column was initially a one-hole case.
- Round 3 fills the remaining `1` and `3`.

This is a concrete discriminator against a one-pass solver and against a solver that only recognizes rows/columns with exactly one blank.

## Implementation choice and limitation

`solution.py` performs exactly three synchronous rounds and fills only singleton candidate sets. It deliberately leaves ambiguous zeros untouched rather than inventing a Latin-square completion. The visible examples do not distinguish “three rounds” from “repeat to fixed point” after convergence; three rounds is the smallest bounded rule that handles the observed dependency chain.
