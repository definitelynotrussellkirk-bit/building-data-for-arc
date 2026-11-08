# 5d15679fbc44

0-bg grid (h~8-11, w~9-12) with: (a) cell (0, 0) holds a KEY color (non-zero); (b) elsewhere a 4-conn BLOB of size 4-5 in the SAME key color (strictly larger than any other key-color region); (c) 1-2 DISTRACTOR blobs of 2-3 cells in other colors. Rule: read key = at(0, 0). Find all 4-conn components of color = key EXCLUDING the (0, 0) cell itself. Pick the LARGEST such blob. Output = that blob cropped to its bounding box (preserving its shape; cells off-shape become 0).

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
