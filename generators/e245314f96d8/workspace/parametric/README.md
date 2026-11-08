# Contact-neighborhood native family

This family preserves the selected canonical `cardinal` program byte-for-byte
and adds `contact_neighborhood=king`.  Same-color four-connected segmentation
is unchanged.  Only the contact graph changes: cardinal uses the four orthogonal
offsets, while king also includes four diagonal offsets.

Sequential dependency:

1. **A — segment and measure contacts:** segment the input into same-color
   four-connected objects, build the selected contact graph, and emit its
   input-dependent per-object degree vector.
2. **Intermediate:** exact object cells, graph adjacency lists, and degree vector.
3. **B — degree-driven paint:** map each degree through `0->3, 1->4, 2->6,
   3+->8` and repaint every cell of that object.

Substituting the cardinal degree vector into a king episode changes the final
output; `solve_from_intermediate` exposes that bounded wrong-intermediate
ablation.  Inputs are identical across settings, prefix stable for 2–6 demos
and 1–4 queries, and include four distinct queries.  The final query is a 30×30
stress grid with 100 objects and 400 occupied cells touching every boundary.

The first two demonstrations contain diagonal chains, mixed crosses, and 2×2
checker contacts.  `audit_episode` rejects the opposite neighborhood,
diagonal-only, half-diagonal, constant-isolation, identity, input-color, size,
and reading-rank competitors.  `audit.py` replays that bounded bank, verifies
protected Racket labels, and also guards the repaired production sampler against
the retained finite-template shortcut by requiring at least 48 D4-normalized
`all_degrees` morphologies and all three degree-2/3/4 spine topologies.
