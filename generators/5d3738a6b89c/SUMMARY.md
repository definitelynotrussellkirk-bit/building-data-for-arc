# 5d3738a6b89c — Prototype dictionary stamping

Two to four 3×3 prototype boxes sit above a full color-9 separator row. Each prototype uses one distinct key color and includes its center. Every matching key below the separator is expanded by stamping that prototype's nonzero mask, retaining only cells inside the grid and below the separator.

The reviewed sampler varies height (11–15), prototype count (2–4), mask size (2–6), colors, positions, and an exact `interior|mixed` edge mode. Every generated input has two nonoverlapping anchors per key. `mixed` inputs construct both separator clipping and outer-grid clipping; a period-3 `mixed, mixed, interior` schedule preserves an outer-clipping witness in every two-demo lesson and every held-out query rotation.

Kind: `per_puzzle`. Reviewed version: `4.2.0`. Canonical rule hash: `f9d79bf79624` (unchanged).

## Semantic coverage

- `first_anchor_per_key_only` fits all three canonical pairs but is refuted by every generated input.
- `outer_border_anchor_ignored` also fits all canonical pairs and is refuted by every scheduled mixed lesson.
- Exact `mask_size=2, edge_mode=mixed` remains legal and exercises true clipping, but its sole non-center outer offset is clipped; default mixed lessons therefore use mask size 3–6 so the outer-border rival is observably wrong.
- `workspace/reference_probe.py` independently parses, stamps, identifies clipping surfaces, implements both rivals, checks overlap, and audits canonical and generated scenes.

Focused verification: 12 clipping regressions failed against version 4.0.0 while all prior 36 passed; the later query-rotation regression failed against version 4.1.0; version 4.2.0 passes 49/49. Independent audit: 180 samples in each of three bands, all 540 valid, deterministic, distinct, and nonoverlapping; 360 mixed scenes exercised both clipping surfaces and refuted the outer-border rival, and all 36 period/query rotations retained that refutation. The executable schedule receipt, strict override gate, and 27/27 Racket/oracle cross-check passed.
