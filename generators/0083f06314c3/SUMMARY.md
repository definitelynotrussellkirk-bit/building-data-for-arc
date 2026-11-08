# 0083f06314c3

Four color-9-separated panels contain template A, template B, a selector, and a search board. Selector color 2 chooses A; any other selector color chooses B. Crop the chosen template, match its nonzero cells in the board in the original orientation and exact colors (crop zeros are wildcards), then recolor the union of all matching template cells to 8.

Kind: `per_puzzle`. Reviewed candidate version: `4.1.0`.
Approval is derived by the catalog from current code and retained evidence.

The candidate keeps 50% canonical anchors and adds one overlapping-match witness
per same-seed four-example default lesson. Selector 1 is now reachable. Panel-internal color 9 is rejected; all cells must be integer ARC colors.
See `workspace/README.md` for executable review tools and exact verification.
