# Solve from the examples

DO NOT consult the Racket rule during this solve.
Also keep generator source, reference solutions, private labels, and prior solution notes closed.
The visible examples below are derived from challenge.json, with dimensions before every grid.
Use only these examples and your own Python experiments. Earlier rule exposure must be recorded.

Write solution.py with solve(grid), record your work in SOLVE_NOTES.md, then from the packet root run:

```sh
python3 review.py solve check --intent solve --note 'Hypothesis and why I tested this revision'
python3 review.py solve finish --earlier-exposure yes --reference-consulted no --reason 'Why I stopped'
```

Every check freezes your code and work log. Feedback covers visible examples and execution only.
Private query correctness is withheld and independently checked after return.
If generation is blocked, fix the generator first and rerun prepare; failures remain recorded.

## Visible examples

```text
Coordinates: zero-based (row, column), top-left; rows down, columns right.
Input and output shapes may differ.

Train example 0
Input: 8 rows × 13 columns. Output: 8 rows × 6 columns.
Input colors/counts: {"0": 78, "3": 4, "5": 8, "6": 4, "8": 6, "9": 4}
Input grid:
[
  [8, 0, 9, 0, 0, 0, 5, 8, 0, 9, 0, 0, 0],
  [8, 0, 0, 0, 0, 9, 5, 8, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 5, 0, 0, 3, 0, 0, 0],
  [0, 0, 0, 0, 6, 0, 5, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 9, 0, 0, 5, 0, 0, 0, 3, 0, 0],
  [0, 0, 3, 0, 0, 0, 5, 0, 0, 3, 0, 0, 0],
  [8, 0, 0, 0, 6, 0, 5, 0, 0, 0, 0, 6, 6]
]
Output colors/counts: {"0": 37, "1": 2, "2": 2, "3": 1, "6": 2, "8": 2, "9": 2}
Output grid:
[
  [8, 0, 9, 0, 0, 0],
  [8, 0, 0, 0, 0, 2],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 1, 0, 0, 0],
  [0, 0, 0, 0, 6, 0],
  [0, 0, 0, 9, 0, 0],
  [0, 0, 3, 0, 0, 0],
  [2, 0, 0, 0, 6, 1]
]

Train example 1
Input: 12 rows × 19 columns. Output: 12 rows × 9 columns.
Input colors/counts: {"0": 189, "3": 7, "5": 12, "6": 6, "7": 7, "9": 7}
Input grid:
[
  [9, 0, 0, 0, 0, 0, 0, 6, 7, 5, 3, 0, 0, 0, 0, 3, 0, 7, 7],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 3, 0, 0, 0, 0, 0, 0, 5, 0, 0, 3, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 7, 0, 0, 0, 5, 0, 0, 0, 0, 0, 7, 0, 0, 6],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 3, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [7, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 9, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 9, 9, 0, 0, 3, 5, 0, 0, 0, 0, 0, 9, 0, 0, 3],
  [6, 0, 6, 0, 0, 0, 0, 0, 0, 5, 6, 0, 7, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 9, 6, 0, 0, 0, 0, 0, 0, 5, 0, 9, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 91, "1": 3, "2": 4, "3": 2, "6": 3, "7": 2, "9": 3}
Output grid:
[
  [9, 0, 0, 0, 0, 1, 0, 6, 7],
  [0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 3, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 7, 0, 0, 1],
  [0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 2, 0],
  [2, 0, 1, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 2, 9, 0, 0, 3],
  [6, 0, 6, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 9, 2, 0, 0, 0, 0, 0, 0]
]

Train example 2
Input: 10 rows × 21 columns. Output: 10 rows × 10 columns.
Input colors/counts: {"0": 184, "5": 10, "6": 8, "8": 8}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
  [0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
  [0, 0, 0, 0, 8, 0, 0, 6, 0, 0, 5, 0, 0, 0, 0, 8, 0, 0, 8, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0]
]
Output colors/counts: {"0": 91, "1": 1, "2": 1, "6": 4, "8": 3}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 6, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
  [0, 0, 0, 8, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
  [0, 0, 0, 0, 8, 0, 0, 6, 0, 0],
  [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 6, 0]
]

Train example 3
Input: 6 rows × 9 columns. Output: 6 rows × 4 columns.
Input colors/counts: {"0": 38, "4": 4, "5": 6, "7": 6}
Input grid:
[
  [7, 0, 0, 0, 5, 7, 0, 0, 0],
  [0, 0, 0, 4, 5, 0, 0, 0, 7],
  [7, 0, 7, 0, 5, 0, 0, 7, 0],
  [4, 0, 0, 0, 5, 4, 0, 4, 0],
  [0, 0, 0, 0, 5, 0, 0, 0, 0],
  [0, 0, 0, 0, 5, 0, 0, 0, 0]
]
Output colors/counts: {"0": 18, "1": 1, "2": 1, "4": 2, "7": 2}
Output grid:
[
  [7, 0, 0, 0],
  [0, 0, 0, 4],
  [2, 0, 7, 0],
  [4, 0, 1, 0],
  [0, 0, 0, 0],
  [0, 0, 0, 0]
]

Test query 0
Input: 8 rows × 13 columns. Output: unknown.
Input colors/counts: {"0": 78, "3": 4, "4": 6, "5": 8, "6": 4, "9": 4}
Input grid:
[
  [3, 0, 0, 0, 6, 6, 5, 3, 0, 0, 0, 6, 4],
  [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
  [0, 9, 0, 0, 0, 3, 5, 0, 9, 0, 0, 0, 0],
  [0, 0, 3, 4, 0, 0, 5, 0, 0, 9, 4, 0, 0],
  [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 4, 0, 5, 0, 0, 9, 0, 4, 6]
]

Test query 1
Input: 12 rows × 19 columns. Output: unknown.
Input colors/counts: {"0": 189, "4": 7, "5": 12, "7": 6, "8": 7, "9": 7}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [4, 0, 0, 0, 0, 0, 0, 0, 0, 5, 4, 0, 0, 0, 0, 0, 0, 0, 0],
  [7, 0, 0, 0, 0, 0, 9, 0, 0, 5, 8, 7, 0, 0, 0, 0, 9, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 7, 0, 0, 5, 0, 0, 0, 0, 0, 0, 7, 0, 0],
  [7, 9, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [8, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 9, 0, 0, 0, 0, 0, 7, 5, 0, 0, 9, 0, 0, 0, 0, 0, 8],
  [0, 0, 0, 0, 0, 0, 0, 0, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 4, 0, 0, 0, 0, 4, 5, 0, 0, 0, 4, 0, 0, 0, 9, 0],
  [0, 4, 0, 0, 0, 0, 0, 0, 0, 5, 0, 9, 0, 0, 0, 4, 0, 0, 0],
  [0, 0, 8, 0, 0, 0, 0, 0, 0, 5, 0, 0, 8, 0, 0, 0, 0, 0, 0]
]
```
