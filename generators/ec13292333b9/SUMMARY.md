# ec13292333b9

Two equal-size panels (h x pw) separated by one full vertical 9-col. Each panel holds sparse non-zero cells (one color per panel; color is irrelevant to the rule). The patterns are built with GUARANTEED PARTIAL overlap: >=1 position occupied in BOTH panels (cancels) and >=1 position unique to each side (survives). Rule: split on the 9-col; output (panel size) is 8 at every position where EXACTLY ONE panel is occupied (XOR of occupancy). Partial overlap makes XOR distinguishable from OR/AND.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
