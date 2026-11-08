# Working notes: 0281fbec1cf2

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native largest-pocket proposal (2026-10-24)

- Preserved the production generator and exact canonical blocker-aware red-ray program. Added a task-local native family with `finish=rays_only` and `finish=largest_pocket`.
- The sequential variant first applies the canonical red-ray expansion, then recomputes four-connected zero regions on that intermediate, selects the unique largest newly enclosed pocket, and fills it with the adjacent blocker marker's color. The enclosed target does not exist before Stage A.
- The deterministic sampler supports 2–6 demonstrations and 1–4 prefix-stable queries with identical inputs across settings; query 0 is 30×30. Public turns reveal one input-only query at a time and do not expose settings, programs, future queries, or labels.
- A broad 128-seed structural sweep covered 292 generation jobs and 2,560 maximum-episode pairs. It exposed seed 104, where two nominally inert corner decoys could cap an extra pocket; decoy selection now rejects candidates that change the intended Stage-A pocket signature.
- Final evidence: 27 focused tests and 36 isolated task tests passed; native qualification covered both settings at seeds 0 and 17 with 32 protected-Racket labels; the finite rival audit plus causal witness executed 74 protected-Racket evaluations; 16 public turn files passed the scoped export checker.
- Source binding: production generator `074f2bad074d925d9b39b7e71a7c743031c47406a85c4893e7020de521c55bc9`; canonical Racket `02b458e5f6e265674740fa37facab026465106b764f3814257714bfcde73164e`; largest-pocket Racket `843528279378c6c6c9d8cdde66668a8b04397e2a97229eb05bc76f0df895a8bb`; manifest `a6e228ace9dd15980aee79c6b4bc0c4c2785b4ca9d97a5df7c536e0b00cdcb6b`.
- Remaining owner action: integrate these exact bytes, rerun native qualification and the source-bound sequential witness, then perform fresh acceptance. This reviewer-ready result does not claim owner acceptance, universal identifiability, training gain, or training admission.
