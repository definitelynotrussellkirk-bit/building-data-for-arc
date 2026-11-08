# 0b6935859da0

Grid (h, w~3-14) with INPUT DECORATION drawn from 5 patterns: all_zero/random (40% density)/sparse (15%)/blob (half-grid solid block)/border_decoy (non-8 colored border). Input colors are irrelevant — only h and w matter for the rule. Output uniq_out=39 (intrinsic — h×w combinations only). Rule (EMIT h×w GRID WITH 0-INTERIOR AND 8-BORDER): COMPUTE h and w from input dims. EMIT a FRESH h×w OUTPUT GRID where: BORDER CELLS (row 0, row h-1, col 0, col w-1) = COLOR-8 (cyan); INTERIOR CELLS = 0. Input contents IGNORED. Net: any grid → same-sized hollow 8-frame.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
