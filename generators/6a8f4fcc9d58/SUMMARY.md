# 6a8f4fcc9d58

0-bg grid (h~9-12, w~10-14) with 3-5 ISOLATED 4-conn components, each in a distinct non-bg color and with a STRICTLY DISTINCT cell count (sizes drawn from {1..7}). Components are separated by background. Rule: extract all 4-conn non-bg components. Sort them by size DESCENDING (with each size unique by construction). Output is a 1×N row where N = number of components, each cell = the color of the corresponding component in size-rank order. Net: a histogram-by-rank single-row encoding.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
