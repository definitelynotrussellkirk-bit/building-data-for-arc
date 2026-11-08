# Working notes: 8b6a2892a064

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.


## Current source-bound recovery proposal

The recovered review contains an exact replayable15-file repair/prototype delta, but its audit seed is missing. It remains unselected and grants no source/variant/training approval. Main/blind identity and byte replay passed; no new generator/tests/Racket run occurred. Current continuation: recover the genuine audit draw record or independently rebase/review the delta. Evidence: `generators/8b6a2892a064/workspace/proposals/recovery-2d2c8c4d08f6dabe/manifest.json`.

## Current native parametric build — 2026-10-25

Built a source-bound `rotation_scope` family without changing the approved production generator or canonical authority. `all_components` returns the selected canonical Racket source exactly; `modal_length` first extracts all straight components, counts their odd lengths, selects the unique modal length, and rotates only components in that input-dependent class.

The family supports independently requested 2–6 demonstrations and 1–4 queries while always storing four distinct queries. The retained curriculum reaches 14×16, 18×20, 24×27, and 30×30; the largest case contains 12 components and 84 foreground cells. Sequential public projection exposes one query input per turn and is prefix-stable with single-query generation.

A bounded protected-Racket audit covered 12 episodes across both settings, seeds 0/17, and demonstration counts 2/3/6: 92 label claims, 41 distinct Racket executions, 16 saved public turns, eight executable rivals, and zero findings. Native qualification passed both settings on both qualification seeds with three demonstrations, four queries, and 40 protected-Racket evaluations. The retained wrong-modal-length witness changes the qualified 30×30 output and was replayed through protected Racket.

The final staged task suite also exposed two old test-authority assumptions: canonical data was derived from the task directory, and formatting-distinct but whitespace-equivalent duplicate Racket sources were compared byte-for-byte. The test now uses `reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, derives the data root from the canonical path, and compares duplicate authority sources under the repository's normalized rule-hash convention. Final task result: 38 passed.

Limits: the adversarial family is finite and does not prove universal identifiability. Owner exact-source integration, fresh native qualification/witness replay, and explicit acceptance remain pending; no training admission is claimed.
