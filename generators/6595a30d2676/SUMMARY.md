# 6595a30d2676

0-bg grid with several rectangular FRAMES (square outlines, side in {5,7,9}) whose color is in {1,2,3,4} (the per-frame ROTATION KEY: 1=identity, 2=CW, 3=180, 4=CCW). Each frame encloses a random inner polyomino in a color from {5,6,7,8,9}. Frames are >=2 cells apart so each is its own component. Rule: for every {1,2,3,4}-colored frame, crop the interior shape, ROTATE it by (frame_color - 1) quarter-turns, re-centre it in the interior, and keep the frame. Output size == input size.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
