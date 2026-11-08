# de83dfd70673

0-bg grid (h ∈ 8-12, w ∈ 9-14, by difficulty) with: TARGET ∈ 1-3 HOLLOW ONE-CELL-THICK RECTANGULAR FRAMES, each of size rh × rw (rh ∈ 3-5, rw ∈ 3-6) drawn at non-overlapping interior positions (via _free padding check), each in a DISTINCT color drawn at random from {1..9}. Each frame's INTERIOR (cells strictly inside the outline) starts EMPTY (0); each frame is non-touching with others. Rule (FILL EACH HOLLOW RECTANGULAR FRAME'S INTERIOR WITH THE SAME COLOR AS THE FRAME — TURNING IT INTO A SOLID RECTANGLE): For EACH color-c frame: COMPUTE its bbox. For EVERY (r, c) inside the bbox (including interior and outline): PAINT g[r][c] = c. The frame outline stays color c (no change); the interior 0-cells become c. Net: each hollow frame becomes a solid same-color block of identical dimensions.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
