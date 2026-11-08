# 8ac8cc86cc49

Fixed 11×11 0-bg grid structured as a 3×3 MACROGRID of 3×3 MACRO CELLS separated by 1-cell SEPARATORS (rows 3, 7 and cols 3, 7 are separator gaps). Each macro cell at (tr, tc) for tr, tc ∈ {0, 1, 2}: occupies rows tr*4..tr*4+2 × cols tc*4..tc*4+2 (3×3). One CLEAN TEMPLATE macro cell (the top-left at (0, 0)) contains a 3×3 PATTERN using TWO COLORS (majority_color and minority_color, both non-{0, 5}). The TEMPLATE variant ∈ {diag, corner, bar}. ALL OTHER 8 macro cells are filled with COLOR 5 (gray) — i.e., the template is the only non-5 macro cell. Rule: identify the TEMPLATE (the macro cell that contains NO COLOR 5 — the 'clean' template). For EACH OTHER macro cell (currently all-5), STAMP the template's pattern at the corresponding macro-cell position — where template has MINORITY color (the 2 in the encoding), KEEP that macro cell as 5; where template has MAJORITY color (the 1), CLEAR the macro cell to 0. Net: template controls which macro cells stay 5 and which become 0 across the 3×3 macrogrid.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
