# c2478bfbf97e

Grid n × n (n = 2*cell_size + 1, cell_size ∈ {3, 4}) with: (a) full color-4 (yellow) SEPARATOR row at row cell_size and full color-4 separator column at col cell_size — splits grid into 4 SECTIONS; (b) one MARKER cell in distinct non-{0, 1, 4} color in each of two sections (top-left, bottom-left). (c) BLUE (color-1) cells scattered in the right-column sections. Rule: for each blue cell, look at its section's row position relative to separator and inherit the marker color from the same-row left-column section (top → m1's color, bottom → m2's color). Output: blue cells replaced by their section-paired marker color.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
