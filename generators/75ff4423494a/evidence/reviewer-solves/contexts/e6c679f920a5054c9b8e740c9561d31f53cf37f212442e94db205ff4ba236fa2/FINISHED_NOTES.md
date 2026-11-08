# Solve notes — 75ff4423494a

This is a human-readable work log written during the post-repair solve episode. It is not a captured token-level model trace.

## Exposure declaration

I had already studied this task's generator and canonical rule while repairing it, so this solve is **not blind** (`earlier_rule_exposure=yes`). During this solve episode I did not reopen the generator, Racket rule, reference solutions, or private labels.

## Visible-example hypothesis

1. Treat orthogonally connected nonzero cells as objects.
2. The largest multi-cell object containing color 8 is the prototype. Its first row-major 8 is the copy origin.
3. Read the prototype through its bounding box, retaining zeros as transparent cells.
4. Start from an all-zero output and stamp the prototype at its original origin and at every other color-8 cell outside the selected prototype.
5. Ignore unrelated foreground cells outside the prototype, except that external 8s are destinations.
6. When two nonzero stamps write different colors to the same cell, output 9. Equal writes remain unchanged. Clip copies at the grid boundary.

Evidence in the visible examples:
- Example 0 has an unrelated color-1 singleton that disappears, while adjacent external 8s create an overlap and a 9.
- Example 1 shows that the origin is the 8 inside the prototype, not necessarily the bounding-box top-left, and the stray color-7 singleton disappears.
- Example 2 has three external 8 destinations and several conflicting overlaps, producing multiple 9s.

I implemented this rule directly in Python. No failed natural revision preceded it because the visible examples, together with acknowledged earlier exposure, made the intended rule unambiguous.
