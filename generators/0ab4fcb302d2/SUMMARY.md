# 0ab4fcb302d2

Version **3.2.0** is pinned to canonical rule hash `39724c7d06e2`.

A lawful input is a 3×3 ARC grid with one all-zero row, one all-zero column, one red marker, and three cells of one shared nonzero non-red color. Removing the gap row and column leaves a 2×2 code. A red marker on the code's main diagonal selects the two main-diagonal 4×4 output blocks; an off-diagonal marker selects the two anti-diagonal blocks. The gap row and column become one-cell output gutters.

The four-draw default schedule crosses intended output orientation with gap-index parity and uses a different marker corner in every phase. Seed parity flips the gap-parity assignment, so lessons refute `gap_parity`, `inverse_gap_parity`, `always_main`, and `always_anti` without creating a permanent marker-corner correlation. Exact controls are `gap_row`, `gap_col`, `marker_corner`, and `block_color`.

Focused tests live in `tests/test_generator.py`; the reusable semantic and distribution probe is `workspace/reference_probe.py`.
