# 55f636823047

0-bg grid (h~8-11, w~11-13) with: (a) TWO REFERENCE BLOBS in 2 DISTINCT non-{0, 8} colors with DISTINCT NORMALIZED SHAPES drawn from {L_TROMINO_NE, L_TROMINO_SE, T_TETROMINO, SQUARE_2X2, V_LINE_3, H_LINE_3}; (b) ONE COLOR-8 (cyan) QUERY BLOB whose normalized shape MATCHES the FIRST REFERENCE blob (placed[0]). All blobs are placed without 4-touching (1-cell padding). Rule (RECOLOR QUERY TO MATCHING REFERENCE, ERASE NON-MATCH): identify the 8-QUERY and the 2 REFERENCE blobs. For each REFERENCE, check if its normalized shape EQUALS the query's. RECOLOR the 8-query in the MATCHING reference's COLOR. ERASE the other (non-matching) reference. Net: query inherits the color of its shape-twin reference; the lone shape vanishes.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
