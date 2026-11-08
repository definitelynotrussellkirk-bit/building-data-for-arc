# 7147e98f8173

0-bg grid (h~10-14, w~12-17) with: (a) ONE COLOR-1 (blue) CORNER CONTROL CELL at one of the 4 corners (rotation indicator: TL=0°, TR=90°, BR=180°, BL=270°); (b) a COLOR-2 (red) ASYMMETRIC TEMPLATE — a small 3-cell L-shape painted at (2, 2); (c) a COLOR-3 (green) MARKER at (0, w-4) and (d) a COLOR-6 (orange) MARKER at (3, w-2). The shifted transformed copy stays in-bounds. Rule: read the BLUE CORNER position as the ROTATION COMMAND. ROTATE the RED TEMPLATE by that angle (90° per TL→TR→BR→BL hop). COMPUTE the GREEN→ORANGE VECTOR (dr = orange_r - green_r, dc = orange_c - green_c). EMIT a BLANK COLOR-8 (cyan) OUTPUT GRID. PAINT the rotated template shifted by the vector onto the cyan canvas at the marker's offset. Net: corner-coded rotation + marker vector = positioned template on cyan.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
