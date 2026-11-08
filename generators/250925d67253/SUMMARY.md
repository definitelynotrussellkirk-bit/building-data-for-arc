# 250925d67253

A fixed 19×19 zero lattice separates nine 5×5 panels. All panel interiors share one nonzero background color and one nonzero marker color. For each source panel, compute the arithmetic centroid of every marker cell; threshold its local row and column at `<1.5`, `<=2.5`, and `>2.5` to select one of the nine row-major destination slots. The nine selected slots form a bijection, and the complete 5×5 source panel is copied to its destination while the zero separators remain fixed.

The sampler uses independent non-cyclic permutations rather than one global shift. It exposes exact controls for permutation kind, marker density, and palette band. Asymmetric motifs make every emitted input disagree with bounding-box-center, nearest-anchor, and coordinate-median substitutes for the arithmetic centroid; four demonstrations identify all declared rivals under every query rotation tested.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical rule hash: `9f1390aa0494`.
