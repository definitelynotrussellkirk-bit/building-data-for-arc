# d39f2d5ed593

0-bg grid (h~8-13, w~9-15) framed by a COLOR-5 (gray) OUTER WALL BORDER (entire row 0, row h-1, col 0, col w-1 painted 5). Inside: (a) ONE COLOR-2 (red) SEED at (r, mid-2); (b) ONE COLOR-3 (green) SEED at (r, mid+2) where r is a random interior row and mid = w // 2 (seeds separated by 4 cols). Otherwise the interior is empty. Rule: APPLY WALL-AWARE BFS from EACH SEED through bg cells (4-conn, walls 5 block). Compute distance to RED and distance to GREEN for every open cell. PARTITION cells: closer to RED → paint red color; closer to GREEN → green color; TIE → tie marker color. Seeds and walls stay. Net: maze interior gets partitioned by BFS distance to seeds, with ties marked separately.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
