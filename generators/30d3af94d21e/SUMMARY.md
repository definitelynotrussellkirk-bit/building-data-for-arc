# 30d3af94d21e

Find the unique singleton non-background color and use its column as the scanline reference.  The other non-background color marks row boundaries. On a marker row, fill between the nearest marker strictly left of the seed column and the nearest marker at-or-right of it; a missing side opens to the grid edge.  Rows strictly between the first and last marker rows that have no markers fill edge-to-edge.  Rows above/below inherit the first/last marker-row interval.  Preserve all marker cells.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
