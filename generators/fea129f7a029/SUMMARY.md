# fea129f7a029

0-bg grid split by ONE full-width row of 5s (the divider). ABOVE it: 'key' shapes, each a random polyomino (2-6 cells) in a distinct non-{3,5} color. BELOW it: 'target' shapes in color 3. Each target is paired to one key by SIGNATURE = (cell count, sorted bbox dims {min,max}) — orientation-independent — and the key/target shapes may DIFFER (e.g. transposed) so long as the signature matches. Key signatures are pairwise distinct so each match is unique. The grid may also include DECOY keys (signature used by no target) and UNMATCHED targets (signature matched by no key). Rule: for each color-3 object, find the non-{3,5} key with equal size and equal sorted bbox dims; if found, recolor the 3-object to that key's color, else leave it as 3.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
