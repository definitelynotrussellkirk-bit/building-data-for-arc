# 4c17a205be08 — infer and transfer a crop transform

A canonical input is a 5×17 zero-background grid containing three 5×5 panels, separated by full-height color-9 columns at indices 5 and 11. Tight-crop the nonzero content in panels A and B, infer the unique mapping among identity, clockwise 90°, 180°, counter-clockwise 90°, left-right reflection, and up-down reflection, then apply the same transform to the tight crop in panel C.

Generator version: `3.0.0`. Racket authority hash: `e3805c81bf19` (unchanged).

Ordinary generation stays on the canonical geometry and morphology manifold: palette size 5 or 6; A has 4–6 occupied cells in exactly two colors; C has 3–6 occupied cells in one or two disjoint colors; total non-background component count alternates 6/7; every crop has six distinct legal transform images. The six transform branches are scheduled cyclically, and every five-demonstration lesson includes five distinct branches and at least one branch absent from the canonical examples.

Semantic contracts declare strict canonical shape, per-transform witnesses, fixed-transform/copy-panel rivals, the strongest canonical-only shortcut, and lesson identifiability. `workspace/audit_curriculum.py` gives a fast deterministic audit and exact shortcut witness; protected Racket remains the authority for outputs.
