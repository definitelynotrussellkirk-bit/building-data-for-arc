# 587396c0817d

7-bg grid whose rows mix three kinds: ACTIVE rows with exactly one color-6 anchor plus other non-7 cells, DECOY rows with non-7 cells but no 6, and EMPTY all-7 rows. Rule: per row, if a 6 is present among the non-7 cells, paint an 8-bar whose length is the non-7 count, starting at c6 - idx where idx is the 6's column-rank among the non-7 cells; everything else becomes 7.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
