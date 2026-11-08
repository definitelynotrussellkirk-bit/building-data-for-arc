# Working notes: 1674812130ff

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review 2026-10-23 — review-3592fb07fc769aa3

Production generator SHA-256 `f9ec99dc5c96ddcf8006b79d36116b10c1abc49fa434dc8cb2030efa23459ca9`, canonical rule hash `b91db7bbbbf5`, and exact canonical Racket SHA-256 `b91db7bbbbf56e66fa4c8631114427f125bab0f01e93526e65f9c9436e554e0b` remain unchanged.

Added a separate proposed episode-level parameter prototype under `workspace/parametric/`: `completion_transform=rotate_180|flip_lr`. `rotate_180` is the byte-identical canonical/default program; `flip_lr` changes only the geometric counterpart map. The divider, anchors, writable color 7, one-sided connected source shape, preservation rule, and input sampler stay fixed. Each episode uses one setting, independently exposes demo/query counts, and defaults to two identifying demonstrations plus four distinct queries.

Every retained label is produced by matching Racket and checked against a separate Python diagnostic. Seed 23 retained two same-input episodes; both demonstrations refute the opposite setting and all four query outputs differ. The exact canonical default replayed all four labeled public pairs. Public files hash only visible demonstration pairs and query inputs; hidden setting, seed, programs and query answers remain private.

The final portable staged suite passed 10/10 after repairing the inherited regression test's fixed-depth canonical-data lookup to use `reviewer_support.canonical_pairs`. The bounded adversarial probe covered 3 seeds × 3 difficulty bands × 2 settings at the 1-demo/8-query count boundary: 18 episodes, 162 Racket-labeled pairs, 81 distinct sampled inputs, exact integer cell types and public/private ID behavior, with no finding. The repository's formal reviewer qualifier then passed all four setting/seed jobs (seeds 0 and 17, two demonstrations, four queries) with 32 protected-Racket evaluations. This is qualification only, not owner acceptance or training admission.

Limits: finite seeds and one declared rival only; demonstration identifiability is not proof against every possible program. Production `generator.py` and canonical authority were not edited.

Next useful action: an owner may independently rerun the formal qualifier and decide whether to accept `completion_transform`; this review deliberately performs neither owner acceptance nor training admission.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/1674812130ff/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
