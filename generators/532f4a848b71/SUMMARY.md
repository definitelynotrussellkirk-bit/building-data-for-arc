# 532f4a848b71

0-bg grid (size varies). Row 0 holds n color-9 markers (n in [1, K]). The body (rows 1+) holds K (3-6) connected objects of DISTINCT sizes in distinct non-{0,9} colors at scattered, separated positions. Rule: n = count of row-0 9s; zero them; sort body objects by size descending (tie-break by position); output the bbox crop of the n-th object. The selected object (output shape/size/color) varies with n, the object sizes and shapes.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
