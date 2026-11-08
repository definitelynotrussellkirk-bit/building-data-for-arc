# Blind solve notes — cf5ccd73cfe5

The input contains a large one-cell-thick rectangular frame and a smaller motif
in another color. The output is the frame's bounding box, with the motif enlarged
by independent integer row and column replication so it exactly fills the frame
interior. Background cells in the motif remain background.

Visible checks:

- 3×3 motif into a 3×9 interior gives scale 1×3.
- 3×2 motif into a 12×4 interior gives scale 4×2.
- 3×3 motif into a 6×6 interior gives scale 2×2.

The implementation identifies the frame as the most frequent nonzero color,
crops the other-color motif, computes the two integer scale factors, draws the
frame, and copies each motif cell into its scaled block. It falls back to the
frame crop if the visible divisibility assumptions are violated.
