# dec3e35da2bc

Fixed 6×23 grid, 0-bg. PROTOTYPE shape drawn at (0..4, 0..4) — a small polyomino in some color proto_color. THREE CANDIDATE PANELS at columns [6..10, 12..16, 18..22] each spanning rows 0..4, in distinct candidate colors. EXACTLY ONE candidate's shape is a ROTATION (90°/180°/270°) of the prototype; the other two are unrelated shapes. A TARGET COLOR is placed at (5, 0). Rule: find the candidate panel whose normalized binary mask matches the prototype under some rotation (0°/90°/180°/270°). CROP that candidate, RECOLOR all its cells to the TARGET COLOR at (5, 0). Output: the small recolored crop. Net: prototype + rotation-match selector + target color → output is the matching panel recolored.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
