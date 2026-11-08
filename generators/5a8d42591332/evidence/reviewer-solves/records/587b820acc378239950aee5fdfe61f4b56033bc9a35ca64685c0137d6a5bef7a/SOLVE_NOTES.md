# Solve work log

## Exposure declaration before solving

I had already inspected and repaired this task's generator and had therefore seen the intended count-comparison rule before this post-repair solve. I did not reopen the generator, Racket rule, canonical ledger, reference solutions, or private query labels after `solve_episode.py prepare`; this attempt used only the visible challenge presentation and my own Python.

## Revision 1 — count each header and compare

The three visible examples show an 11×11 matrix with three 2×2 color-1 headers across the top, three 2×2 color-2 headers down the left, and a blank 3×3 array of 2×2 body blocks. For each body block I count the occupied cells in its column header and row header. The output color is 4 when the top count is larger, 3 when the left count is larger, and 8 when they are equal. Separator rows and columns and the original headers are preserved.

I implemented this directly with fixed header starts 3, 6, and 9, copied the input, and filled only the nine body blocks. The main alternative rejected by the visible diagonal/reverse textures is counting only a positional prefix rather than all occupied cells.
