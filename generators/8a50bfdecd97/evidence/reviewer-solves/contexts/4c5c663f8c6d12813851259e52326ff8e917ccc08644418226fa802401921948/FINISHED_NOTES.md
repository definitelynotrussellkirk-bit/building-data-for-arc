# Solve work log

## Prior exposure

I had already inspected and repaired this task's generator before this required post-repair solve, so earlier rule exposure is **yes**. During this solve episode I did not reopen the generator, Racket rule, canonical records, private query labels, or earlier solution explanations. I used only the newly prepared visible `challenge.json` and local Python checks over its public training pairs.

## Revision 1 — move the bitmap to the missing bracket-defined corner

**Visible structure.** Every input has background 7, two disconnected color-4 three-sided brackets in diagonal corners, and one bitmap in a third color. The output preserves both brackets and the bitmap's exact sparse shape, clears the bitmap's source cells to 7, and places it in the fourth corner.

**Row coordinate.** Classify the bitmap as lying on the left or right half. The bracket on that same horizontal side determines the destination's vertical edge: a top-oriented bracket aligns the bitmap's top with its top row; a bottom-oriented bracket aligns the bitmap's bottom with its bottom row.

**Column coordinate.** The bracket on the opposite horizontal side supplies its open interior columns. Place the bitmap inside that interval, aligned toward the bracket's outer side. Training example 0 distinguishes this from an arbitrary left alignment: the right bracket has three interior columns while the bitmap is two columns wide, and the output occupies the two rightmost interior columns.

**Bitmap handling.** Preserve only occupied cells inside the source bounding box rather than filling the box. This matters for the T-shaped and cross-shaped examples. Erase every source cell before stamping the same offsets at the destination.

**Probe.** A visible-example harness first failed on the supplied `NotImplementedError`. After implementing the component/bounding-box procedure, the same harness matched all three visible training outputs exactly.

**Remaining uncertainty.** The visible examples do not show malformed brackets, multiple movable colors, or a bitmap wider than the opposite bracket interior. The implementation stays within the demonstrated domain rather than inventing recovery behavior.
