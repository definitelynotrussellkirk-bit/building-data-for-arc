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
Input: 12 rows × 12 columns. Output: 12 rows × 12 columns.
Input colors/counts: {"0": 121, "7": 12, "8": 11}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0]
]
Output colors/counts: {"0": 117, "4": 8, "7": 10, "8": 9}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4],
  [7, 7, 7, 7, 7, 7, 7, 7, 7, 4, 7, 4],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0]
]

Train example 1
Input: 4 rows × 7 columns. Output: 4 rows × 7 columns.
Input colors/counts: {"0": 18, "1": 4, "9": 6}
Input grid:
[
  [0, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 1, 0, 0],
  [9, 9, 9, 9, 1, 9, 9],
  [0, 0, 0, 0, 1, 0, 0]
]
Output colors/counts: {"0": 14, "1": 2, "4": 8, "9": 4}
Output grid:
[
  [0, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 4, 4, 4, 0],
  [9, 9, 9, 4, 1, 4, 9],
  [0, 0, 0, 4, 4, 4, 0]
]

Train example 2
Input: 5 rows × 4 columns. Output: 5 rows × 4 columns.
Input colors/counts: {"0": 12, "3": 3, "9": 5}
Input grid:
[
  [0, 0, 9, 0],
  [0, 0, 9, 0],
  [0, 0, 9, 0],
  [3, 3, 9, 3],
  [0, 0, 9, 0]
]
Output colors/counts: {"0": 8, "3": 1, "4": 8, "9": 3}
Output grid:
[
  [0, 0, 9, 0],
  [0, 0, 9, 0],
  [0, 4, 4, 4],
  [3, 4, 9, 4],
  [0, 4, 4, 4]
]

Test query 0
Input: 11 rows × 7 columns. Output: unknown.
Input colors/counts: {"0": 60, "4": 10, "5": 7}
Input grid:
[
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [5, 5, 5, 5, 5, 5, 5],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0],
  [0, 4, 0, 0, 0, 0, 0]
]

Test query 1
Input: 6 rows × 6 columns. Output: unknown.
Input colors/counts: {"0": 25, "3": 5, "4": 6}
Input grid:
[
  [0, 0, 0, 0, 3, 0],
  [0, 0, 0, 0, 3, 0],
  [4, 4, 4, 4, 4, 4],
  [0, 0, 0, 0, 3, 0],
  [0, 0, 0, 0, 3, 0],
  [0, 0, 0, 0, 3, 0]
]
```
