# Solve work log

## Exposure declaration before solving

I had already read and repaired this task's generator and canonical semantics before this exposed solve, so this is **not blind**. After `solve_episode.py prepare`, I consulted only the visible train/query presentation and this solve workspace; I did not reopen the generator, Racket source, canonical labels, or earlier solution explanations.

## Revision 1

Visible examples show one blue cell acting as the local origin of every other nonzero, non-red payload cell. The output is a fresh zero canvas with a red destination retained and each payload offset copied from blue to red. Examples 2 and 3 contain two reds; the later red in row-major order is the destination, which rules out first-red. Example 3 loses the translated colour-3 cell beyond the right edge, establishing clipping rather than wraparound or all-or-nothing rejection.

Implementation: scan row-major, retain the unique blue, collect reds and payload, choose `reds[-1]`, paint that red on a blank same-size grid, translate payload by `(destination - blue)`, and keep only in-bounds cells. I expect both visible queries to follow this single rule; no alternative remains that fits the multi-red and clipping demonstrations.
