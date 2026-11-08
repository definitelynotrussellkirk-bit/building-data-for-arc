# Solve from the examples

DO NOT consult the Racket rule during this solve.
Also keep generator source, reference solutions, private labels, and prior solution notes closed.
The visible examples below are derived from challenge.json, with dimensions before every grid.
Use only these examples and your own Python experiments. Earlier rule exposure must be recorded.

Write solution.py with solve(grid), record your work in SOLVE_NOTES.md, then from the packet root run:

```sh
python3 solve_episode.py check --intent solve --note 'Hypothesis and why I tested this revision'
python3 solve_episode.py finish --earlier-exposure yes --reference-consulted no --reason 'Why I stopped'
```

Every check freezes your code and work log. Feedback covers visible examples and execution only.
Private query correctness is withheld and independently checked after return.
If generation is blocked, fix the generator first and rerun prepare; failures remain recorded.

## Visible examples

```text
Coordinates: zero-based (row, column), top-left; rows down, columns right.
Input and output shapes may differ.

Train example 0
Input: 8 rows × 8 columns. Output: 8 rows × 8 columns.
Input colors/counts: {"0": 49, "3": 8, "8": 7}
Input grid:
[
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [8, 8, 8, 8, 3, 8, 8, 8],
  [0, 0, 0, 0, 3, 0, 0, 0]
]
Output colors/counts: {"0": 45, "3": 6, "4": 8, "8": 5}
Output grid:
[
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 4, 4, 4, 0, 0],
  [8, 8, 8, 4, 3, 4, 8, 8],
  [0, 0, 0, 4, 4, 4, 0, 0]
]

Train example 1
Input: 6 rows × 10 columns. Output: 6 rows × 10 columns.
Input colors/counts: {"0": 45, "4": 6, "7": 9}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
  [7, 7, 7, 7, 7, 7, 4, 7, 7, 7],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0]
]
Output colors/counts: {"0": 41, "4": 12, "7": 7}
Output grid:
[
  [0, 0, 0, 0, 0, 4, 4, 4, 0, 0],
  [7, 7, 7, 7, 7, 4, 4, 4, 7, 7],
  [0, 0, 0, 0, 0, 4, 4, 4, 0, 0],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 4, 0, 0, 0]
]

Train example 2
Input: 13 rows × 5 columns. Output: 13 rows × 5 columns.
Input colors/counts: {"0": 48, "3": 5, "4": 12}
Input grid:
[
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [3, 3, 3, 3, 3],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0]
]
Output colors/counts: {"0": 44, "3": 3, "4": 18}
Output grid:
[
  [0, 4, 0, 0, 0],
  [4, 4, 4, 0, 0],
  [4, 3, 4, 3, 3],
  [4, 4, 4, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0],
  [0, 4, 0, 0, 0]
]

Test query 0
Input: 12 rows × 9 columns. Output: unknown.
Input colors/counts: {"0": 88, "5": 9, "7": 11}
Input grid:
[
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [5, 5, 5, 5, 5, 5, 5, 5, 5],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0]
]

Test query 1
Input: 8 rows × 8 columns. Output: unknown.
Input colors/counts: {"0": 49, "4": 7, "7": 8}
Input grid:
[
  [0, 0, 4, 0, 0, 0, 0, 0],
  [7, 7, 7, 7, 7, 7, 7, 7],
  [0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 0, 0, 0, 0, 0]
]
```
