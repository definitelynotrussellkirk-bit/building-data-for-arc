# c8132e595372

0-bg grid (h~9-11, w~11-13) with 3-4 ISOLATED motifs in distinct non-{0,5} colors AND a few color-5 (gray) BLOCKER cells scattered around. Motifs and blockers are separated. Rule: collect blockers (color-5 cells). Extract non-5 components, sort by leftmost column ascending. Start with a fresh empty grid containing only the blockers. For each component in left-to-right order: slide its cells LEFT (dr=0, dc=-1) until they hit a blocker, an already-placed cell, or the grid's left edge. Paint the slid cells with the component's color. Net: gravity-left with both stationary blockers (5) and stacking dynamic blockers from earlier-placed objects.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
