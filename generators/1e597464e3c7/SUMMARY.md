# 1e597464e3c7

0-bg grid (size varies). Row 0 holds 2-5 transform COMMANDS (codes 1-6: id / rot-cw / rot-180 / transpose / flip-lr / flip-ud) in the leftmost cells. Below row 0 sits a single MOTIF (a connected polyomino in one color). Rule: crop the motif, apply each command to it, and pack the transformed copies left-to-right with 1-column gaps (output height = the tallest piece). The grid size, the command sequence, the motif shape and color all vary freely (was a fixed 7x9 motif + sample_index-keyed commands, ~9 distinct).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
