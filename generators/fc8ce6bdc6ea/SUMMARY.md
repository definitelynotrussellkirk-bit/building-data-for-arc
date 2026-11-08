# fc8ce6bdc6ea

0-bg grid divided into 2-6 ADJACENT VERTICAL COLOR REGIONS (left to right), each a distinct color (adjacent regions differ so boundaries are detectable) with a small per-region decoration cell. Region widths are randomized: SOMETIMES all distinct, sometimes with a repeat. Rule: detect the regions by per-column modal color; if ALL region widths are unique, REVERSE the region order; otherwise ROTATE the regions LEFT by one. Columns (including decorations) are copied wholesale. Net: regions flip or cyclically shift depending on whether their widths are all unique.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
