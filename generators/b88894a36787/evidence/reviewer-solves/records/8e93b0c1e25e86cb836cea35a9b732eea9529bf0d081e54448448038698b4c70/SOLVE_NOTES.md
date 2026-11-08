# Solve work log

## Exposure declaration before revision 1

This is the required post-repair exposed solve. I had already inspected and
worked on this task's generator and canonical rule before preparation, so earlier
rule exposure is **yes**. During this solve I used only the visible examples in
`solve/README.md` / `solve/challenge.json` and did not reopen the generator,
Racket source, reference solutions, or private query labels.

## Revision 1 — header-to-side connectors

Observation: row 0 contains a contiguous ordered set of distinct colors. Each
color either has one matching marker on the left or right border, or has no body
marker. In every training output, a matched color is copied vertically from its
header cell through the marker's row and then horizontally along that row to the
marker. A color with no matching border marker continues vertically to the last
row. All other cells stay zero. The examples also suggest header-order priority
if paths ever overlap, though the visible paths are disjoint.

Implementation: collect row-0 `(column, color)` entries, locate each matching
body marker, assign the bottom row when no marker exists, then paint each output
cell from the first header entry whose vertical or horizontal segment covers it.
This directly handles both visible test queries, including the three-header case
and the four-header case with one missing marker.

Remaining uncertainty: no uncertainty about the visible transformation; masked
query correctness remains intentionally unavailable.
