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
Input: 10 rows × 11 columns. Output: 10 rows × 11 columns.
Input colors/counts: {"0": 93, "2": 3, "5": 10, "8": 4}
Input grid:
[
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [2, 2, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 2, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 8, 8, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 8, 8, 0, 0, 0, 0]
]
Output colors/counts: {"0": 90, "2": 3, "3": 3, "5": 10, "8": 4}
Output grid:
[
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [2, 2, 0, 5, 0, 3, 3, 0, 0, 0, 0],
  [0, 2, 0, 5, 0, 3, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 8, 8, 0, 0, 0, 0],
  [0, 0, 0, 5, 0, 8, 8, 0, 0, 0, 0]
]

Train example 1
Input: 12 rows × 10 columns. Output: 12 rows × 10 columns.
Input colors/counts: {"0": 103, "2": 4, "4": 3, "5": 10}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [0, 0, 0, 0, 0, 2, 2, 2, 0, 0],
  [0, 0, 0, 0, 0, 4, 0, 2, 0, 0],
  [0, 0, 0, 0, 0, 4, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 99, "2": 4, "3": 4, "4": 3, "5": 10}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
  [0, 0, 0, 0, 0, 3, 3, 3, 0, 0],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [0, 0, 0, 0, 0, 2, 2, 2, 0, 0],
  [0, 0, 0, 0, 0, 4, 0, 2, 0, 0],
  [0, 0, 0, 0, 0, 4, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

Train example 2
Input: 9 rows × 13 columns. Output: 9 rows × 13 columns.
Input colors/counts: {"0": 101, "2": 4, "5": 9, "7": 3}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 2, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 7, 7, 7, 2, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 2, 2]
]
Output colors/counts: {"0": 97, "2": 4, "3": 4, "5": 9, "7": 3}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 0, 0, 3, 0, 0, 0, 5, 0, 0, 0, 2, 0],
  [0, 0, 0, 3, 0, 0, 0, 5, 7, 7, 7, 2, 0],
  [0, 0, 3, 3, 0, 0, 0, 5, 0, 0, 0, 2, 2]
]

Train example 3
Input: 11 rows × 12 columns. Output: 11 rows × 12 columns.
Input colors/counts: {"0": 114, "2": 3, "5": 12, "9": 3}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [0, 0, 0, 9, 9, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 111, "2": 3, "3": 3, "5": 12, "9": 3}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [0, 0, 0, 9, 9, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0]
]

Test query 0
Input: 10 rows × 11 columns. Output: unknown.
Input colors/counts: {"0": 94, "2": 3, "5": 10, "6": 3}
Input grid:
[
  [0, 0, 0, 0, 6, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 6, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 6, 2, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 2, 2, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0]
]

Test query 1
Input: 12 rows × 10 columns. Output: unknown.
Input colors/counts: {"0": 103, "2": 4, "5": 10, "8": 3}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
  [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 2, 2, 0, 0, 0, 0, 0, 8, 8],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
```
