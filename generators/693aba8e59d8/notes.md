# 693aba8e59d8 review notes

Version 3.0.0 replaces the former 2–3-anchor sampler with the authority-faithful four-anchor task. It pins selected rule hash `60c823b90a2d`, treats color 4 as a counterclockwise quarter turn, uses the selected floor-centered stamp convention, and produces output-only stamps.

The three canonical demonstrations leave a real shortcut: north/east/south/west position predicts rotations 1/2/3/4 because the anchor colors never move. The new `anchor_phase` schedule cyclically permutes colors through those positions. Every four consecutive samples contains all four phases, so any three-demo lesson and every query rotation refutes the position shortcut. Executable rivals also cover ignoring rotations and swapping the two quarter turns.

Five exact pixel-observable axes are exposed (`grid_h`, `grid_w`, `shape_kind`, `base_orientation`, `anchor_phase`). Calls fail closed on unknown or coerced controls. Four asymmetric generated polyomino families, seed-varying phase-safe layouts, strict grammar checks, canonical parity, mutation fixtures, and lesson-level tests are retained in the task folder.

## Parametric review `review-de6fb3d52a32cf07`

Production generator `1f679f1ceaafe69b4edd87c97d47ed0cf1765ae85e48907ce940dc3478bbfdcf` and canonical rule `60c823b90a2d` remain unchanged. The native adapter at `workspace/parametric/adapter.py` adds episode-fixed `rotation_rule`: `anchor_color` returns the canonical source byte-for-byte, while `bbox_area_offset` extracts the connected color-6 base, measures its normalized bounding-box area modulo four, and adds that input-derived offset before rotating/stamping at the visible anchors.

The sampler supports prefix-stable 2–6 demonstrations and 1–4 independent queries with matched inputs across settings. Query four is a substantive 30×30 case touching all four boundaries. Public turns contain demonstrations plus only the current query input; private settings, programs, answers, future queries and query-count hints remain absent.

Retained evidence: `workspace/parametric/evidence/manifest.json`; self-audit in `workspace/parametric/evidence/current/audit.json` (120 protected-Racket evaluations over ten declared programs); native qualification in `checks/693aba8e59d8/qualification/qualification.json` (four jobs, 32 protected-Racket labels) with byte-identical replay; and `checks/693aba8e59d8/sequential-witness.json`, where forcing the measured offset to zero changes 16 final cells on the qualified 30×30 query. Status is reviewer-ready only: owner integration/acceptance is pending and `training_admitted` remains false.
