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
Input: 8 rows × 8 columns. Output: 8 rows × 8 columns.
Input colors/counts: {"0": 60, "3": 2, "4": 2}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [4, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [4, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 56, "3": 4, "4": 4}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 3, 0, 0, 0],
  [4, 0, 0, 0, 3, 0, 0, 0],
  [4, 0, 0, 0, 3, 0, 0, 0],
  [4, 0, 0, 0, 3, 0, 0, 0],
  [4, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]

Train example 1
Input: 7 rows × 10 columns. Output: 7 rows × 10 columns.
Input colors/counts: {"0": 62, "1": 2, "2": 2, "3": 1, "4": 1, "7": 2}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
  [0, 0, 0, 3, 0, 0, 1, 0, 0, 7],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 4, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 1, 0, 2, 7],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 55, "1": 4, "2": 5, "3": 1, "4": 1, "7": 4}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
  [0, 0, 0, 3, 0, 0, 1, 0, 2, 7],
  [0, 0, 0, 0, 0, 0, 1, 0, 2, 7],
  [0, 0, 0, 4, 0, 0, 1, 0, 2, 7],
  [0, 0, 0, 0, 0, 0, 1, 0, 2, 7],
  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

Train example 2
Input: 10 rows × 8 columns. Output: 10 rows × 8 columns.
Input colors/counts: {"0": 73, "1": 2, "3": 2, "6": 1, "8": 2}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0],
  [0, 0, 3, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 8, 6, 0, 0, 0, 0, 0],
  [0, 0, 3, 0, 0, 0, 0, 0],
  [0, 8, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 66, "1": 8, "3": 2, "6": 1, "8": 3}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0],
  [0, 0, 3, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0],
  [0, 8, 6, 0, 0, 1, 0, 0],
  [0, 8, 3, 0, 0, 1, 0, 0],
  [0, 8, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]

Train example 3
Input: 7 rows × 8 columns. Output: 7 rows × 8 columns.
Input colors/counts: {"0": 49, "1": 2, "4": 2, "5": 1, "8": 2}
Input grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 1, 0, 0, 4, 0, 0, 0],
  [8, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 4, 5, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [8, 1, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]
Output colors/counts: {"0": 43, "1": 5, "4": 3, "5": 1, "8": 4}
Output grid:
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 1, 0, 0, 4, 0, 0, 0],
  [8, 1, 0, 0, 4, 0, 0, 0],
  [8, 1, 0, 0, 4, 5, 0, 0],
  [8, 1, 0, 0, 0, 0, 0, 0],
  [8, 1, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]

Test query 0
Input: 6 rows × 6 columns. Output: unknown.
Input colors/counts: {"0": 32, "2": 2, "7": 2}
Input grid:
[
  [0, 0, 7, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 2],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0],
  [0, 0, 7, 0, 0, 2]
]

Test query 1
Input: 9 rows × 8 columns. Output: unknown.
Input colors/counts: {"0": 64, "1": 2, "2": 2, "4": 1, "7": 1, "9": 2}
Input grid:
[
  [1, 0, 2, 0, 4, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 9, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 7, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [1, 0, 0, 0, 0, 0, 0, 0],
  [0, 9, 2, 0, 0, 0, 0, 0]
]
```
