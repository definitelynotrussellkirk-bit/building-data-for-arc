# e6362765bc86

0-bg grid of 3 SQUARE panels (each s×s, s∈3..6) separated by single DIVIDER COLUMNS (color 5) at cols s and 2s+1; total width 3s+2, height s. panel0 holds a BASE MOTIF (random asymmetric cell set in base_color). panel1 holds T(base) where T is a chosen DIHEDRAL TRANSFORM ∈ {id, rot90, rot180, rot270, flip-lr, flip-ud, transpose, anti-transpose}. panel2 holds an INDEPENDENT QUERY MOTIF (random cell set in query_color). Rule (DIHEDRAL ANALOGY): split into 3 panels; INFER the transform T such that T(panel0)==panel1 exactly; APPLY T to panel2 and EMIT it. Net: panel0:panel1 :: panel2:output is a transform analogy; output is s×s.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
