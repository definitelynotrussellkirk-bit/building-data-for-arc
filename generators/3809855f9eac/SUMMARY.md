# 3809855f9eac

0-bg grid with ≥2 connected motifs in distinct non-zero colors (≥1-cell buffer, 3-5 cells each, varied shapes). The rule consumes the FIRST TWO components in bbox-top-left sort order; any additional motifs are ignored by the rule but add visual variety. Rule: sort all connected components by bbox top-left (row-major). Take the first two. Crop each to its bbox. Normalize the pair to a common (max-h × max-w) bounding box. Compute symmetric difference between the two binary masks: output cell = 8 if exactly one of the two masks has a non-zero cell there, else 0. Output size = (max-h × max-w).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
