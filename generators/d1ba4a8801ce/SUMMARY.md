# d1ba4a8801ce

Fixed 13×15 grid. Background is a 2-COLOR CHECKERBOARD with even color (e) at (r%2==0 or c%2==0) and odd color (o) at (r%2==1 and c%2==1). The pattern is DISRUPTED by: (a) a RECTANGULAR FRAME (drawn in some FRAME color) at fixed coords for one of two ORIENTATIONS (horizontal: (3..8, 3..12) or vertical: (2..11, 4..10)); (b) TWO CONTENT BLOCKS in distinct colors A and B placed at fixed offsets relative to the frame. Rule: RESTORE the checkerboard everywhere EXCEPT INSIDE the frame, where the two content blocks are kept CENTERED. The frame border stays. Net: input has a noisy backdrop with a framed layout; output restores the checkerboard outside the frame, centering content blocks inside it.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
