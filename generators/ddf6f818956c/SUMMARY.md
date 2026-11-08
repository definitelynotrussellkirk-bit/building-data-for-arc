# ddf6f818956c

0-bg grid (size varies). A red (color-2) frame defines the reflection box. VERTICAL axis: a full rectangular frame (solid top bar) with 1-3 gray (color-5) markers ABOVE/BELOW it. HORIZONTAL axis: only the LEFT and RIGHT vertical walls (top bar not solid) with markers to the LEFT/RIGHT. Rule: detect the frame bbox; if the top bar is solid reflect each gray vertically across the near top/bottom edge, else reflect horizontally across the near left/right wall; the original gray is removed and the reflection drawn (always in-bounds, landing in the box interior). Grid size, axis, frame size/position and the markers all vary freely (was a fixed 12x12 frame with one marker).

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
