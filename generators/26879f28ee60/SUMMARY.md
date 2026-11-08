# 26879f28ee60

0-bg grid (h ∈ 6-8, w ∈ 9-11) with: (a) ROW 0 CMD SEQUENCE — n_cmds ∈ 1-3 NON-ZERO CMD CELLS in LEADING POSITIONS (cols 0..n_cmds-1), each value ∈ {1..4} (per demos: 1=cw90, 2=flip-LR, 3=flip-UD, 4=transpose); cols n_cmds..w-1 of row 0 stay 0; (b) ONE RANDOM MULTI-COLOR BODY (2-5 x 2-5, varied shape, 1-3 holes) placed below row 0. Rule (READ CMDS FROM ROW 0 LEADING CELLS, CROP THE BODY TO ITS BBOX, APPLY EACH CMD'S TRANSFORM IN ORDER, OUTPUT THE TRANSFORMED CROP): READ cmds from row 0 left-to-right (stop at first 0). CROP the body (rows ≥ 1) to the bbox of non-bg cells. APPLY EACH CMD IN ORDER to the cropped grid: 1=cw90, 2=flip-LR, 3=flip-UD, other=transpose. OUTPUT the final transformed crop. Net: the body is transformed by the cmd sequence; output is its transformed version (dims + content vary with the body).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
