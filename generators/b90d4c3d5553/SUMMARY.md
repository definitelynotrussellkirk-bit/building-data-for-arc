# b90d4c3d5553 — local-frame mirror selection

Two colored tripods define independent source (2/3/4) and target (5/6/7) bases. Color-8 source markers within local Chebyshev radius three copy exactly when their reflected offset `(-u,v)` exists. Axis cells with u=0 are self-mirrors and copy. Other cells, including distant distractors, remain unchanged.

The 2.0.0 input sampler covers all 64 independent cardinal/reflected frame combinations, variable relative positions, h=10..24/w=14..24, 1..6 pairs, 0..4 unpaired cells, 0..5 axis markers, and 0..4 exterior distractors. Counts and advertised overrides are exact and observable from pixels. Source and target padded squares fit and do not overlap. A sparse/broad mixture preserves a canonical-density component without replaying fixed layouts.

Canonical Racket rule hash `a9a48a6b2948` is unchanged. The former validator rejected all three canonical inputs; the revised validator accepts them. Task-local tests and independent geometry checks pass, but reference-runtime qualification is **blocked by unavailable Racket**, not waived. See `workspace/README.md`, `notes.md`, and the returned review/check evidence. Approval remains derived from the catalog and authoritative retained evidence; this summary is not approval.
