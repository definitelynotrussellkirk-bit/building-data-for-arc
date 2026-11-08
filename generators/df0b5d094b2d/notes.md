# Working notes: df0b5d094b2d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-0774c3878e6860bf — parametric rectangle movement

### D1 — Preserve the marker/corner reasoning and canonical default

The production generator remains `90da7d4462f3fd9038a663532c28cc4262c7178fb1cb826844551c20a132b90e`, and the canonical rule hash remains `e4ccb0c97cf3`. Default `move_distance=1` is the exact canonical Racket program (`47a199cf2deb3410c8d79d03aff3da9a8f0f843601a670e3d237c1af751f15d5`).

### D2 — Parameterize only diagonal move distance

The prototype adds `move_distance ∈ {1,2}`. Both settings infer color 8 as the missing-corner marker, reconstruct the same full rectangle, erase the same source, and move toward the marker on the same diagonal. The alternative changes only the signed displacement magnitude; its program hash is `526330aee71395eca54fd191f0e9599e6d36cea7a7a0399300443ade68734e1e`.

### D3 — Use one setting-neutral sampler for both distances

All scenes reserve margin for the two-cell move, so changing the hidden setting never changes the sampled input. The adapter supports 2–6 demonstrations and 1–8 queries independently. The reviewed four-query schedule is 10×10, 16×20, 24×26, and 30×30; the largest query contains four widely separated substantive rectangles and spans at least 20 rows and columns.

### D4 — Reject overlapping or ambiguous source evidence

A 10×10 construction initially placed mixed 3×4/4×3 rectangles so their source cells touched and one paint operation erased the other rectangle's missing-corner evidence. The sampler now uses nonoverlapping 3×3 small-scene rectangles; the parser correctly rejects any ambiguous or overwritten source rather than repairing labels after the fact.

### D5 — Fix exact public serialization and portable test lookup

Public evidence now writes exact `public_challenge_bytes`, after an adversarial saved-file check exposed pretty-JSON/full-SHA drift. Label tampering, query-output leakage, and unsupported counts fail closed. The legacy generator test also replaced a fixed `Path(__file__).parents[...]` canonical lookup with `reviewer_support.find_root`/`canonical_pairs`; the staged preflight failure is retained as a red receipt.

### D6 — Retain as a bounded proposal

Focused Racket-backed tests passed 16/16. The staged suite passed 24 tests plus 12 subtests after the portable-path fix; one inherited `GenCtx._drawn` deprecation warning remains. The source inventory is `workspace/parametric/evidence/source-inventory.json` (SHA-256 `9e9a1b832346537c4504a90e2d57d7f47e3f8a9e090cd2d6b5bb637887c5363f`). Owner qualification with fresh seeds remains the next action; no variant acceptance, production change, or training admission is claimed.
