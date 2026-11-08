# 54701bc5970a

0-bg grid (h~9-11, w~11-13) with: (a) ONE COLOR-1 (blue) PROTOTYPE SHAPE drawn from a 5-shape BANK (L-tromino, S-tetromino, T-tetromino, 2×2, J-tetromino); (b) TWO COLOR-2 (red) CANDIDATE SHAPES — ONE is a REFLECTION (identity/flip-lr/flip-ud/rotate-180) of the prototype (equivalent under D2), ONE is a DIFFERENT shape from the bank. All shapes placed non-overlapping with 1-cell padding. Rule (RECOLOR REFLECTION-MATCHING CANDIDATE TO 8): identify the COLOR-1 PROTOTYPE and its normalized cell set. For EACH COLOR-2 candidate: COMPUTE its normalized cell set. CHECK if it equals the prototype under any of {identity, flip-lr, flip-ud, rotate-180}. If YES, RECOLOR that candidate to COLOR-8 (cyan). Non-matching candidates stay color 2. Prototype stays. Net: the red shape shape-equivalent to the blue prototype becomes cyan.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
