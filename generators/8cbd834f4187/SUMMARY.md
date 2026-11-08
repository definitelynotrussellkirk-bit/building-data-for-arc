# 8cbd834f4187

A 3xW strip (W is 19 or 29) has all-zero outer rows. Row 1 contains 2 or 3 distinct seed colors at the first triangular columns: [0,1] or [0,1,3]. Read those colors left-to-right as a sequence. For k=0,1,..., paint row 1, column k(k+1)/2 with seed[k mod n] while that column fits. All non-triangular cells remain unchanged (and are zero in lawful inputs).

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
