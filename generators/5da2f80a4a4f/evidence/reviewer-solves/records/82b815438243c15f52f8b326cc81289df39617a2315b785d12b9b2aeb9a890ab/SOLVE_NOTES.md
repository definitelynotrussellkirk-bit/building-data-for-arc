# Solve work log

## Prior exposure

I had already inspected this task's generator and canonical rule while repairing it, so this is an **exposed post-repair solve**, not a blind solve. During this solve phase I used only the prepared visible examples, this Python file, and the solve checker; I did not reopen the generator, Racket rule, reference solutions, private query labels, or prior solution explanations.

## Revision 1

The three visible examples show a hollow color-2 rectangle. Inside it is one dense nonzero, non-2 rectangular key, possibly offset from the frame. The output discards the surrounding canvas and key offset, preserves the frame's bounding-box dimensions, and enlarges the key independently in rows and columns so it exactly fills the frame interior.

Evidence from the examples:

- Example 0: a 2x2 key fills a 4x4 interior by 2x2 replication.
- Example 1: a visibly repeated 4x4 key compresses to a 2x2 pattern, then fills an 8x8 interior by 4x4 replication. More generally, extracting the full dense key bounding box and scaling it still gives the shown output.
- Example 2: a 4x2 key fills an 8x10 interior by row scale 2 and column scale 5, showing that row and column factors can differ.

Implementation plan: locate the color-2 bounding box; locate the non-{0,2} key bounding box strictly inside it; crop that key; compute exact integer row/column scale factors from the frame interior; return a color-2 border around the independently replicated key. I included shape and divisibility checks so malformed inputs fail rather than silently producing a misleading grid.

Alternative rejected: copying the key at its original offset or assuming a fixed 2x scale. Both are contradicted by the examples, especially example 2.
