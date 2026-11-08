# 5df36dd2c804

0-bg grid (h, w ~14-22) with 1-2 GRAY (color-5) rectangular CONTAINERS, each ≥3 rows × ≥4 cols, with ONE GAP in the top row (gap column varies — left, center, or right lean). Containers have ≥2 rows of bg margin above. Rule: detect each gray container. FILL its INTERIOR (cells inside the container border, excluding the border itself) with color 2 (red). Then SHOOT a vertical color-2 ray UPWARD from the GAP cell to the top of the grid (or until obstacle). Net: each container gets red-filled and emits a rising red ray through its gap.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
