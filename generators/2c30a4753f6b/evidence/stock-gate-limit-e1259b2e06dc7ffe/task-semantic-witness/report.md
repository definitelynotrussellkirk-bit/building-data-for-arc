# F1 — Short-line heuristic assessed against the task

Generator SHA-256: `5cfd714cdb89a82d64a954f20b6306d0cc53d8daa9fa862f6df9ba5fdb4f19d4`.

The exact linter helpers were compiled from the current linter AST and run on its first six easy inputs, seed = sample_index = 1..6. All 30 named minimal mutations were checked. Exactly one was accepted: the short_line mutation of seed/index 2, a 4x5 grid whose only nonzero row is row 2 `[6,6,6,6,0]`. It belongs to the declared near_symmetric profile: four foreground cells, zero as unique modal background, and exactly one mismatched opposing column pair. The actual canonical Racket authority executed this exact input without error and produced the expected 4x10 reflection.

This is task-semantic evidence that the named shape is lawful, not a reason to claim the strict linter passed. The strict lint warning and failed exit remain retained; no exception or shared code change was introduced. See `probe.py`, `report.json`, and `racket.json`.

The new small teaching geometry was additionally checked for 1000 seeds 0..999 at sample_index 2*seed, easy. All 1000 inputs pass self_check and independently refute all six declared rivals; widths exceed 3, exactly two foreground colors are present, and area is at most 36. Observable profile counts: 896 multicolor_sparse and 104 edge_asymmetry. These overlapping classifications do not change the demonstrated reflection semantics. This is finite evidence, not exhaustive support coverage.

Correction to an earlier chat update: foreground color 2 was a transcription error conflating seed 2 with its color. Retained reproduction and Racket receipt both use color 6; their exact inputs were asserted equal.
