# 0b6b3a286ad0

Five separator-delimited panels encode `KEY1 → VALUE1` and `KEY2 → VALUE2`.
The query is scanned in the shown orientation: nonzero `KEY1` cells must match,
while zero cells are wildcards. A `KEY1` match selects `VALUE1`; otherwise the
validated generator domain contains an exact `KEY2` match and selects `VALUE2`.

Version `4.0.0` emits only the two canonical profiles (`6×25×5` and `7×26×5`)
and uses a deterministic five-example curriculum:

1. exact `KEY1` match,
2. exact `KEY2` only,
3. rotated `KEY1` decoy plus `KEY2`,
4. one-cell `KEY1` near miss plus `KEY2`,
5. `KEY1` with colored cells under its zero wildcard positions.

The semantic observer, declared rivals, witness hooks, lesson-identifiability
check, exact override observer, and task-local regression suite are part of the
selected implementation. The canonical Racket authority is unchanged; the
Python `rule_mirror` exists only for tests and semantic diagnostics.
