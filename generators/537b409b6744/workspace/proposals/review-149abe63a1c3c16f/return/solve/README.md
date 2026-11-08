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
Input: 10 rows × 10 columns. Output: 10 rows × 10 columns.
Input colors/counts: {"2": 9, "4": 1, "6": 2, "7": 88}
Input grid:
[
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 4, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 6, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 6, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 2, 2, 2, 7],
  [7, 7, 7, 7, 7, 7, 2, 2, 2, 7],
  [7, 7, 7, 7, 7, 7, 2, 2, 2, 7]
]
Output colors/counts: {"2": 12, "4": 1, "6": 2, "7": 85}
Output grid:
[
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 4, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 2, 2, 7, 2, 2],
  [7, 7, 7, 7, 7, 2, 2, 6, 2, 2],
  [7, 7, 7, 7, 7, 2, 2, 6, 2, 2]
]

Train example 1
Input: 13 rows × 14 columns. Output: 13 rows × 14 columns.
Input colors/counts: {"0": 162, "2": 3, "4": 15, "6": 2}
Input grid:
[
  [0, 0, 0, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 6, 6, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 162, "2": 3, "4": 15, "6": 2}
Output grid:
[
  [0, 0, 4, 4, 4, 4, 6, 6, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 4, 4, 4, 0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 4, 4, 4, 4, 0, 0, 4, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

Train example 2
Input: 11 rows × 11 columns. Output: 11 rows × 11 columns.
Input colors/counts: {"1": 9, "4": 1, "5": 109, "6": 2}
Input grid:
[
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
  [5, 5, 5, 5, 5, 6, 6, 5, 1, 1, 1],
  [5, 5, 5, 5, 4, 5, 5, 5, 1, 1, 1],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
]
Output colors/counts: {"1": 12, "4": 1, "5": 106, "6": 2}
Output grid:
[
  [5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
  [5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6],
  [5, 5, 5, 5, 4, 5, 5, 5, 1, 1, 1],
  [5, 5, 5, 5, 5, 5, 5, 5, 1, 1, 1],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
]

Test query 0
Input: 10 rows × 13 columns. Output: unknown.
Input colors/counts: {"2": 117, "4": 1, "5": 3, "7": 9}
Input grid:
[
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
  [7, 7, 7, 2, 2, 5, 2, 2, 2, 2, 2, 2, 2],
  [7, 7, 7, 2, 2, 5, 5, 2, 2, 2, 2, 2, 2],
  [7, 7, 7, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2],
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
]

Test query 1
Input: 10 rows × 10 columns. Output: unknown.
Input colors/counts: {"0": 8, "3": 4, "6": 2, "7": 86}
Input grid:
[
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 6, 6, 7, 7, 7],
  [7, 7, 7, 7, 3, 3, 7, 7, 7, 7],
  [7, 7, 7, 7, 3, 3, 7, 7, 7, 7],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [7, 7, 7, 7, 0, 0, 0, 0, 7, 7],
  [7, 7, 7, 7, 0, 0, 0, 0, 7, 7]
]
```
