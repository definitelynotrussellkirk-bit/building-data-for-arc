# Solve work log

I had no earlier exposure to this task's rule, generator, reference solutions, or private labels. I used only the visible `challenge.json` examples and local experiments over those examples.

## Revision 1 — nested-region tree

Observed that only four-connected zero regions not touching the border change. The non-8 colors in the first column form an ordered key. A plain nesting-depth rule fails on training example 1: its two sibling inner chambers remain color 4 rather than advancing to color 2.

Hypothesis: bounded zero regions form a containment tree. Roots receive key color 0. A node with exactly one nested child advances that child to the next key color; when a node branches into several children, those siblings inherit the current key color. A region whose index exceeds the available key remains zero. This explains all three demonstrations, including the unused final key in example 0, the branching case in example 1, and the uncolored deepest center in example 2.

Probe: I extracted four-connected zero components, their bounding boxes, and visible output colors. Component areas / colors were:

- example 0: 25→4, unique child 8→9;
- example 1: 28→4, two sibling children 6→4 and 6→4;
- example 2: 32→7, unique child 16→6, unique grandchild 1→0 because the key is exhausted.

I first wrote `test_visible_solution.py`; it failed on the untouched `NotImplementedError`, then implemented the tree rule. Remaining uncertainty: bounding-box containment is inferred from the visible family; unusually interleaved non-nested regions would need a stronger planar-containment test, but no visible instance has that structure.
