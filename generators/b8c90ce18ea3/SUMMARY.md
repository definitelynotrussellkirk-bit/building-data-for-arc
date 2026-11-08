# b8c90ce18ea3

0-bg grid (h, w~5-8) with SPARSE NONZERO CELLS scattered at 4-7 random positions using a 3-5 color palette drawn from 1..9. Cells are placed at random distinct positions; no spatial structure or invariant. Always at least one nonzero mark. Rule (SCAN-ORDER EMIT): READ the grid in ROW-MAJOR SCAN ORDER (top-to-bottom, left-to-right). COLLECT every nonzero value in ENCOUNTER ORDER into a list. EMIT them as a SINGLE-ROW OUTPUT (1 × N grid where N is the number of nonzero cells). Output preserves: (a) the scan order, NOT the input positions; (b) repeated colors appear as separate entries (no dedup); (c) sorted order is irrelevant. Net: scattered marks → 1-row sequence in scan order.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
