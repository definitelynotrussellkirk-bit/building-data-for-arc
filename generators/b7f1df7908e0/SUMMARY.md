# b7f1df7908e0

0-bg grid (~10-13 × 12-15) split into 4 QUADRANTS by EXACTLY ONE full-width color-9 (maroon) ROW and EXACTLY ONE full-height color-9 COLUMN. The LOWER-LEFT QUADRANT contains EXACTLY ONE HOLLOW RECTANGULAR FRAME (border-only, ~3×3 to 5×5) in some non-{0, 9} color, with its strict interior all-0. Other quadrants are empty. Rule: identify the hollow object in the lower-left quadrant. COMPUTE its bbox CROP and SOLID-FILL its interior (replace 0 cells inside the bbox with the object's color). PASTE the now-SOLID rectangle into the LOWER-RIGHT QUADRANT at the same relative bbox position. The lower-left frame STAYS hollow. The 9-dividers and the original frame stay. Net: the hollow frame in the bottom-left gets duplicated as a solid filled rectangle in the bottom-right.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
