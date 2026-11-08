# f615ee46cf27

A room MAZE: a grid of rectangular rooms (0 interiors) separated by color-1 WALLS, connected by color-7 DOORS placed along a random spanning TREE so the room-adjacency graph is a tree. Rule: build the room graph from the doors, find its articulation-point rooms (whose removal disconnects the graph) and paint them color 8; leaf rooms stay 0; walls and doors stay. Net: the 'cut-vertex' rooms light up. A tree guarantees both painted (internal) and unpainted (leaf) rooms. (Was: random scattered motifs unrelated to the rule.)

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
