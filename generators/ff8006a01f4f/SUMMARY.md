# ff8006a01f4f

0-bg grid (h~4-12, w~6-16) where each row starts with a contiguous non-zero PREFIX of random length 1-6 and random colors from {1..9} (some rows may be blank), followed by zeros to the row end. Rule: for each row, identify the leading non-zero prefix pattern. TILE that prefix REPEATEDLY across the full row width (modular index — the prefix pattern repeats c mod prefix_len). Net: each row becomes a periodic tiling of its initial prefix.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
