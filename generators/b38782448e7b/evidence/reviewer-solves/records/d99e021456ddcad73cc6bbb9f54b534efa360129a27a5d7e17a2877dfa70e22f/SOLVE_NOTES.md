# Solve notes

The background is the unique modal color. Non-background cells in the top row
are candidate vertical controls. Comparing the demonstrations shows that a top
cell fires only when row 1 in the same column differs from it; equal row-0/row-1
pairs are decoys and their columns remain unchanged.

For each firing column, preserve the top marker and transform every later cell
by an XOR-like toggle against that marker: marker-colored cells become
background, while background or any third color becomes the marker. Every other
column is preserved. This explains the large object slices, third-color
replacement, marker holes, and inert top controls in all three visible examples.
