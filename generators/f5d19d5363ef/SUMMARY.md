# f5d19d5363ef

0-bg grid (h, w ∈ 9-18) with: N_FRAMES ∈ 3-6 NESTED COLOR-1 RECTANGULAR FRAMES (concentric, each smaller than the last) with RANDOMIZED OUTER POSITION and OFFSETS — outermost frame anchored at random (or0, oc0) with size (oh, ow), each inner frame inset by a random (dr, dc) ≥ 1 from the previous on each side. All frames have STRICTLY DISTINCT bbox areas. Rule (SORT 1-FRAMES BY BBOX AREA DESCENDING; ASSIGN EACH FRAME (BY DEPTH RANK 0 = OUTERMOST) A COLOR FROM PALETTE [2,4,6,7,3,9]; RECOLOR EVERY CELL OF THAT FRAME TO THE ASSIGNED COLOR): EXTRACT all 1-frames. SORT by bbox area descending. For rank i: RECOLOR frame i with palette[i] ∈ [2,4,6,7,3,9]. Net: nested 1-frames recolored by nesting depth.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
