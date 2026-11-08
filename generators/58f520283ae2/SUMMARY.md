# 58f520283ae2

0-bg grid (size varies). Cell (0,0) holds a COMMAND in {1..7}; the rest of the grid holds ONE MOTIF: a random multi-color pattern with a NON-SQUARE bounding box (bh != bw, each 2-4, 2-3 colors, every bbox edge touched so the crop is exact). Rule: read the command; crop-to-content of the rest; apply the transform (1=identity, 2=rotate-cw, 3=rotate-180, 4=transpose, 5=flip-lr, 6=flip-ud, else=transpose). Output = the transformed motif (dims swap under rotate/transpose). The non-square bbox makes every command distinguishable.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
