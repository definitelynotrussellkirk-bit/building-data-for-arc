# Solve work log

Earlier exposure before this solve: none to task `69b886e1df03`; I did not open its generator, rule, notes, solutions, labels, or audit records. I had only read the packet-level instructions and the visible `challenge.json`.

## Revision 1 — complete non-degenerate component bounding boxes

Hypothesis: each colored 4-connected component that spans at least two rows and two columns is an incomplete filled rectangle. Fill zero cells inside that component's bounding box. Leave horizontal bars, vertical bars, and singletons unchanged.

Evidence from the visible training pairs:

- The 9-colored L in training 0 becomes a 2×2 rectangle.
- The 6- and 7-colored T shapes in training 0 become 2×3 rectangles.
- The 2-colored L and 4-colored U-like shape in training 1 become 2×2 and 2×3 rectangles.
- The 1-colored T in training 2 becomes a 2×3 rectangle.
- Existing one-cell-wide bars of lengths 2 or 3 remain unchanged in every example.

Implementation: find 4-connected components independently, compute each bounding box, and fill only background cells when both box dimensions exceed one. Processing components separately matters because the second test input has two disconnected color-4 objects with different roles.

Probe: `/tmp/test_blind_69b886e1df03.py` replays all three visible training examples. The initial stub failed with `NotImplementedError`, establishing the test, before this implementation was written.

Remaining uncertainty: an unseen lesson could contain another color inside a component's bounding box. I preserve nonzero cells rather than overwrite them. The examples do not distinguish 4-connectivity from grouping all cells of a color, but the disconnected same-color objects in test input 1 make component-local processing the safer inferred rule.
