# Working notes: 89a9a629c544

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current reviewer decision — 2026-10-26

The prior source declared independent per-color vertical flips but sampled layers whose transformed masks could overwrite another color before its turn. The retained audit seed `(100004, 4, easy)` reproduced the count loss. Version 1.2.0 now constructs ordinary layers in disjoint transform-closed tiles, validates the declared two-color/asymmetry constraints, and compares exact sequential semantics against the independent target masks. Degenerate controls remain deliberately outside `self_check`.

Focused evidence: `generators/89a9a629c544/tests/test_generator_89a9a629c544.py` and packet receipt `checks/89a9a629c544-tests-task1/`. The selected canonical Racket source and canonical labels are unchanged.

## Native parametric family — ready for owner source review

`workspace/parametric/` now declares `axis_policy=vertical|anchor_bbox`. The default file is the exact selected canonical source. The alternate counts colors, chooses the unique maximum, derives `lr` or `ud` from that anchor's shape-hash dimensions, and applies the result to every layer. A protected-Racket self-review covered both settings, seeds 0/17, demo counts 2/3/6, four queries, 136 evaluations, and named shortcuts; no bounded finding survived. Base preflight and the wrong-intermediate causal witness passed under the bundled protected runtime.

Current handoff evidence:
- `workspace/parametric/evidence/current/self_review.json`
- `workspace/parametric/evidence/manifest.json`
- packet `checks/89a9a629c544/qualification/`
- packet `checks/89a9a629c544/causal/witness.json`

Limits: this is authoring/preflight evidence only. Owner qualification/acceptance and training admission remain unperformed.
