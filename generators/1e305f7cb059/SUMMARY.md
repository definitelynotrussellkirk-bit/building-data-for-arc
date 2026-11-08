# 1e305f7cb059

0-bg grid (h~8-10, w~11-13) with 1-2 HOLLOW RECTANGULAR FRAMES (5×5 or 5×6 or 6×5 or 6×6 border-only) drawn in distinct non-bg FRAME COLORS. Each frame contains EXACTLY ONE SEED CELL at a random interior position, in a DIFFERENT non-bg SEED COLOR. Frames are 4-conn isolated from each other. Rule: for each hollow frame, identify the single SEED COLOR inside it. FILL every cell of the frame's strict INTERIOR with that SEED COLOR (replace the interior 0s — and the seed itself — with seed_color). The frame border stays in its original frame color. Net: each frame's empty interior gets flooded with the color of the single seed marker that was inside.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
