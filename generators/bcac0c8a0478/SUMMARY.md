# bcac0c8a0478

Dense color-8 mazes with one start (2), goal (3), and mandatory checkpoint (5).
Color 6 and 7 pairs are symmetric immediate portals. The selected rule runs BFS
in `(row, column, checkpoint_seen)` state and paints only traversed zero cells 4.

Version `2.0.0` replaces unconstrained marker placement with constructive maze
search. Every ordinary sample refutes the canonical-fitting goal-first shortcut,
a direct-to-goal shortcut, and (when portals are present) an ignore-portals
shortcut. Exact overrides, strict canonical profiles, semantic witnesses, and a
source-bound independent oracle are covered by task-local tests.

Kind: `per_puzzle`. Canonical rule hash: `076228df68df`.
