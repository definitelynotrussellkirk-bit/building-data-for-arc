# ce40117f40f9

0-bg grid (h×w, ~7-10 by ~7-10) with: (a) one connected BLOB of 2-4 cells in some non-{0, 9} color, placed in the upper-left quadrant; (b) one COLOR-9 (maroon) MARKER cell in the lower-right area, placed so the blob's bbox fits within bounds when translated to start at the marker's position. Rule: detect the marker and the blob. Crop blob to bbox. Build fresh 0-canvas. Paste cropped blob with its top-left corner at the marker position. Output: blob moved to marker position; original blob and marker cells cleared.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
