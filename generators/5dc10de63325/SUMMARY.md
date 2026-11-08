# 5dc10de63325

Count all cyan cells, floor-divide by four, and repeat the prescribed 2×2 glyph in four quadrants of a 5×5 output. The middle row and column remain zero. Within each quadrant, the fixed fill order is bottom-right, bottom-left, top-right, then top-left.

| Input cyan count | Cyan cells per quadrant |
| --- | --- |
| 4–7 | 1 |
| 8–11 | 2 |
| 12–15 | 3 |
| 16–19 | 4 |

Ordinary inputs contain only integer colors 0 and 8, retain a zero background, and have height and width independently in 5–18. Connectivity and shape do not affect the answer. The five distributions are `clustered`, `row_aligned`, `block`, `snake`, and `scattered`. Explicit dimensions and cyan counts are exact; `texture` aliases `distribution`.

The canonical ledger has 14 labeled records representing seven unique pairs, all 6×6 with counts 12 or 16. It includes a disconnected 6+6 cyan example. The broader dimensions and counts 4–19 are deliberate extensions supported by the selected Racket rule.

**Request ten demonstrations for the reviewed lesson design:** CLI `--train 10 --test 1`, or Python `n_train=10, n_test=1`. `Catalog.generate` defaults to three demonstrations and does not infer this requirement from `EXAMPLES_NEEDED = 10`. Raw eleven-draw schedule windows supply repeated low-glyph and rounding witnesses. Separate checks of accepted lessons and their filtering limits are recorded in [notes.md](notes.md).

Kind: `per_puzzle`. Version: `4.0.0`. Selected rule hash: `f2b1ab0d6fcb`. Authoritative labels come from Racket. Approval remains derived from the current source and retained evidence.
