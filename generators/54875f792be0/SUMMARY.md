# 54875f792be0

0-bg grid with: (a) N (1-3) hollow rectangle FRAMES (h≥3, w≥3, cells form only the bbox border); (b) M (1-3) DISTRACTOR shapes — solid rectangles or irregular shapes. All objects in distinct colors. Rule: extract every connected non-bg component. For each, check if it's a frame: h≥3, w≥3, size = perimeter = 2(h+w) - 4, and all cells on bbox border. Keep frames (preserve colors), drop all non-frames. Output: fresh 0-grid with only the frames.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
