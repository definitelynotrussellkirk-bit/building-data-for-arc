# 1e56158e4892

Fixed 5×23 0-bg grid with 4 PANELS at FIXED cols [0..4], [6..10], [12..16], [18..22] (each 5×5, separated by empty divider cols). Each panel contains 3-7 cells of a single distinct non-zero color at random positions. Rule: SPLIT into 4 panels. BINARIZE each. COMPUTE the ROTATION-EQUIVALENCE class of each panel under the 4 rotations (0°, 90°, 180°, 270°). Build a 4×4 OUTPUT MATRIX: cell (i, j) = 8 if i == j (diagonal); else 1 if normalized binaries of panel i and panel j are EXACTLY EQUAL (identical shape); else 2 if rotation-equivalent (same rotation orbit but different orientation); else 0. Net: 4×4 matrix encoding panel rotation-relations.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
