# 9817b8e4d47f

0-bg grid (h~9-12, w~10-13) with 3-4 NON-TOUCHING BLOBS at scattered positions, each in a DISTINCT color from 1..9. Blob sizes are MIXED — 2 from PRIMES {2, 3, 5, 7} + 1-2 from COMPOSITES {4, 6}. So at least one prime-sized and one composite-sized blob exist. Rule (RECOLOR BY BLOB SIZE PRIMALITY): for EACH BLOB (4-conn connected component), COUNT its cells (size). If the SIZE is PRIME (2, 3, 5, 7), RECOLOR the blob to COLOR 2 (red). If COMPOSITE (4, 6), RECOLOR to COLOR 8 (cyan). Net: blobs get binary-recolored by primality of size — prime→red, composite→cyan.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
