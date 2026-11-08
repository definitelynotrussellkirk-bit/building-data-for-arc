# 81d29e66f427

Row 0 holds ordered operation keys above two equal colour-5 frames. The left
interior is mask A in colour 2 and the right interior is mask B in colour 3.
The unchanged canonical rule emits one colour-8 panel per key: `2 = A OR B`,
`3 = A AND B`, and every other non-zero key is `A XOR B`.

Generator version `3.0.0` keeps canonical geometry in every difficulty band,
adds broader dimensions/gaps/key counts, makes all advertised overrides exact
and pixel-observable, realizes all four Boolean truth states in default masks,
and uses a three-example schedule containing both key 4 and a non-4 XOR key.
The semantic contract explicitly tests all-OR, all-AND, all-XOR, fixed-order,
and key-4-only-XOR rivals.

Kind: `per_puzzle`. Racket authority hash: `dfc8cc699169` (unchanged).
Approval is derived by the catalog from current code and retained evidence.
