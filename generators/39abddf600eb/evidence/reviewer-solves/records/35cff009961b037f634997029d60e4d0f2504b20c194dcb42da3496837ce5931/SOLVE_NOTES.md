# Visible-only blind solve

## Scope

Read only `README.md` and `challenge.json` from this solve directory, plus my own work and checker feedback. No earlier rule exposure; no generator, Racket rule, canonical data, audit, reference solution, prior solution, or private labels consulted.

## Hypothesis and experiment

The dominant nonzero color forms a rectangular frame around two single-cell markers. Preserve the input dimensions and values; change an empty interior cell to color `9` exactly when its Manhattan distances to the two markers are equal. Marker colors do not enter the distance calculation.

A Python experiment reading only `challenge.json` extracted the frame bounds and markers, generated this distance locus, and compared the entire predicted grids against the visible outputs. The experiment exited 0 and matched all 3 of 3 training outputs exactly. Added-cell counts were 7, 7, and 5. The second example distinguishes this hypothesis: its locus is `(3,3)` through `(3,8)`, plus `(4,9)` (zero-based coordinates).

| Item | Input shape, rows × columns | Visible output / predicted output shape |
| --- | --- | --- |
| Train 0 | 11 × 13 | Visible: 11 × 13 |
| Train 1 | 11 × 13 | Visible: 11 × 13 |
| Train 2 | 10 × 12 | Visible: 10 × 12 |
| Query 0 | 12 × 13 | Predicted: 12 × 13; reference unknown |
| Query 1 | 9 × 14 | Predicted: 9 × 14; reference unknown |

The hypothesis predicts no added cells for query 0, whose markers have odd Manhattan separation. It predicts four added cells in query 1: `(2,6)`, `(3,6)`, `(4,6)`, `(5,6)`. These are predictions, not verified query results.

## Implementation and check record

Implemented the first candidate in `solution.py`; there have been no revisions or manufactured failures. The implementation selects the dominant nonzero frame color, uses its bounding box, requires two interior markers, and paints only empty interior cells at equal Manhattan distance.

Planned official check, run from the outer workspace as instructed:

```sh
python3 review.py blind check --intent solve --note 'Equal Manhattan distance inside the rectangular frame matches all three visible examples; test the first implementation and query execution.'
```

The scope of evidence is the three visible examples. Query correctness remains masked. Other grid structures are not established by the visible examples.
