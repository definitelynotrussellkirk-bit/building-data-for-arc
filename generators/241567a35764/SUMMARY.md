# 241567a35764

0-bg grid (h~11-15, w~13-18) with: (a) ONE COLOR-1 (blue) TEMPLATE drawn from 6 asymmetric tetromino shapes at top-left position; (b) ONE ROTATION CONTROL cell in COLOR ∈ {2, 3, 4} on the BOTTOM BORDER encoding rotation; (c) optionally ONE COLOR-6 FLIP CONTROL adjacent (±2 cols) to the rotation control; (d) MARKER PAIR — COLOR-7 cell at (r7, c7) and COLOR-8 cell at (r8, c8) (interior, ≥2-cell vector between them, allowing ≥2 in-bounds stamps). Rule (STAMP ROTATED+FLIPPED TEMPLATE IN MAROON ALONG 7→8 VECTOR): READ rotation control (determines k = 0/1/2 CW rotations or D4 code). READ optional FLIP-6 (toggle horizontal flip). APPLY transform to the BLUE TEMPLATE. COMPUTE delta = (r8 - r7, c8 - c7). STAMP the transformed template in COLOR-9 (maroon) at the 7-marker position, then at successive offsets (+delta) until off-grid. Net: blue template + rotation control → maroon stamps repeated along the 7→8 vector path.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
