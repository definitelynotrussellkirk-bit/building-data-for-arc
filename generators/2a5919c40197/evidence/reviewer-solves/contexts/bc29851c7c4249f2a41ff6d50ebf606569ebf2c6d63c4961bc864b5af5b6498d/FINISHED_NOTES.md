# Solve notes — 2a5919c40197

## Visible-only hypothesis

The output preserves the input dimensions and classifies rows independently.
A row becomes entirely gray (`5`) when every cell in that row has the same
input color; otherwise the complete row becomes black (`0`). The identity of
the input color does not matter.

## Evidence from the visible examples

- Example 0: the mixed first row becomes `0`; the two uniform rows become `5`.
- Example 1: all eleven uniform length-9 rows become `5`, while the five rows
  containing at least one disagreement become `0`, including rows whose first
  several cells agree before a later change.
- Example 2: only the uniform middle row becomes `5`.

## Alternatives rejected

- Column classification is inconsistent with every visible output: outputs are
  constant across each row, and rows with mixed columns are still classified
  according to their own contents.
- Majority-color or threshold rules are refuted by a row with a single changed
  cell: it is entirely `0`, despite an overwhelming majority.
- Inspecting only the first three cells is refuted by the wide example, where
  rows beginning with repeated values but changing later become `0`.

## Implementation

`solve(grid)` checks full-row uniformity with `len(set(row)) == 1` and emits a
same-width row of `5` or `0`. No reference source was consulted during this
solve phase. I had earlier exposure to the family while reviewing its generator,
so this is not claimed as a blind solve.
