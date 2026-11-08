# Solve from the examples

DO NOT consult the Racket rule during this solve.
Also keep generator source, reference solutions, private labels, and prior solution notes closed.
The visible examples below are derived from challenge.json, with dimensions before every grid.
Use only these examples and your own Python experiments. Earlier rule exposure must be recorded.

Write solution.py with solve(grid), record your work in SOLVE_NOTES.md, then from the packet root run:

```sh
python3 review.py blind check --intent solve --note 'Hypothesis and why I tested this revision'
python3 review.py blind finish --earlier-exposure no --reference-consulted no --reason 'Why I stopped'
```

Every check freezes your code and work log. Feedback covers visible examples and execution only.
Private query correctness is withheld and independently checked after return.
If blind generation is blocked, retain that result; do not edit this untouched generator.

## Visible examples

```text
Coordinates: zero-based (row, column), top-left; rows down, columns right.
Input and output shapes may differ.

Train example 0
Input: 12 rows × 13 columns. Output: 3 rows × 3 columns.
Input colors/counts: {"0": 135, "2": 6, "4": 6, "5": 4, "7": 5}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 4, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 4, 4, 4],
  [0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 4, 4, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 5, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0]
]
Output colors/counts: {"0": 3, "2": 6}
Output grid:
[
  [2, 2, 2],
  [0, 2, 0],
  [2, 2, 0]
]

Train example 1
Input: 11 rows × 13 columns. Output: 4 rows × 3 columns.
Input colors/counts: {"0": 122, "1": 6, "7": 9, "8": 6}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0],
  [0, 0, 7, 7, 0, 0, 0, 0, 0, 8, 0, 0, 0],
  [0, 0, 7, 7, 0, 0, 0, 0, 0, 8, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 7, 0, 0, 0, 0, 0, 1, 0, 0, 0],
  [0, 0, 0, 7, 0, 0, 0, 0, 0, 1, 0, 0, 0],
  [0, 0, 0, 7, 0, 0, 0, 1, 1, 1, 0, 0, 0],
  [0, 0, 0, 7, 0, 0, 0, 0, 1, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 6, "8": 6}
Output grid:
[
  [8, 0, 0],
  [8, 0, 0],
  [8, 0, 0],
  [8, 8, 8]
]

Train example 2
Input: 10 rows × 12 columns. Output: 4 rows × 3 columns.
Input colors/counts: {"0": 95, "2": 11, "5": 4, "6": 7, "7": 3}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0],
  [0, 6, 6, 0, 0, 0, 0, 2, 2, 2, 0, 0],
  [0, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 6, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
  [0, 6, 0, 0, 0, 0, 5, 5, 0, 2, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 5, 0, 2, 2, 2],
  [0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 2],
  [0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0, 2]
]
Output colors/counts: {"0": 5, "6": 7}
Output grid:
[
  [6, 6, 0],
  [6, 6, 6],
  [6, 0, 0],
  [6, 0, 0]
]

Test query 0
Input: 12 rows × 11 columns. Output: unknown.
Input colors/counts: {"0": 114, "3": 6, "5": 5, "6": 7}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0],
  [0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 6, 6, 0, 6, 0, 0, 0, 0],
  [0, 0, 0, 6, 6, 6, 6, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

Test query 1
Input: 11 rows × 13 columns. Output: unknown.
Input colors/counts: {"0": 120, "1": 8, "3": 8, "6": 7}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 1],
  [0, 0, 0, 0, 3, 3, 0, 3, 0, 1, 0, 1, 1],
  [0, 0, 0, 0, 0, 3, 3, 3, 0, 1, 1, 1, 1],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 6, 6, 6, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
```
