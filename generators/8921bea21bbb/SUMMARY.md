# 8921bea21bbb

A full-height color-9 column separates equal-width panels. Every nonzero cell in the left panel is a binary keep mask: copy the corresponding right-panel color into the output, and write 0 wherever the left panel is 0.

The v3 sampler uses an exact five-axis contract (`panel_h`, `panel_w`, `mask_count`, `mask_color`, `right_zero_count`) over 5–8-row/column panels. Its four-slot teaching schedule alternates canonical 5×5 and 6×6 color-2 profiles with non-color-2 masks and right-panel holes, so lessons preserve canonical support while refuting the strongest canonical-only shortcut (“only color 2 is a mask”).

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `adbc411a920b`.
Approval remains derived by the catalog from current code and retained evidence.
