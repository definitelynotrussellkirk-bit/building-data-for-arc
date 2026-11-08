# b07ab22c1245

0-bg grid (h ∈ 9-11, w ∈ 12-14) with: (a) TWO HOLLOW COLOR-5 (GRAY) RECTANGULAR FRAMES, each height 4-5 and width 4, drawn via draw_rect_outline at FIXED corner regions: FRAME 1 at top-left (1, 1)..(fr, fc), FRAME 2 at bottom-right (h-fr2-1, w-fc2-1)..(h-2, w-2); (b) IN EACH FRAME'S INTERIOR: ONE MARKER CELL of a distinct non-{0, 5} color drawn from {2, 3, 4, 6, 7, 8} (palette[0] for frame 1, palette[1] for frame 2), at a random interior position; (c) ONE COLOR-6 NOISE CELL at (0, w-1). Rule (FOR EACH CLOSED 5-FRAME, FILL EVERY 0-CELL INSIDE THE FRAME'S INTERIOR WITH THE MARKER COLOR INSIDE THAT FRAME): EXTRACT every COLOR-5 frame outline. For EACH frame: READ the unique non-{0, 5} MARKER COLOR inside. PAINT every interior 0-cell with the marker color. The frame outline stays gray; the marker cell stays its color. Net: each frame's interior floods with its marker color; gray outlines and noise cells preserved.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
