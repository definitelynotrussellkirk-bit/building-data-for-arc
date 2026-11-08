# a99e79b52aa4

15×16 grid (0-bg) with 2-3 hollow rectangular FRAMES (border-only rectangles) in distinct non-zero colors. Each frame's interior contains 2-4 non-zero pattern cells in a color DIFFERENT from its frame color (and different from any other frame's color). Frames don't overlap. Rule: detect all rectangular hollow frames. Sort them by frame color ascending. For each frame, extract its interior (cells strictly inside the border): keep cells whose color is not 0 and not the frame color. Crop the interior to its bounding box. Build a gallery: stack all cropped interiors LEFT-TO-RIGHT, TOP-ALIGNED, with a 1-cell gap between them. Output height = max of crop heights; width = sum of crop widths + (n-1) gaps.

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
