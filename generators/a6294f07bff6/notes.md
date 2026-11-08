# Working notes: a6294f07bff6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a6294f07bff6/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current review decision — 2026-10-25

- Left the production generator unchanged; its ordinary asymmetric scenes already exercise the exact canonical vertical flip.
- Added a native two-setting family under `workspace/parametric/`: exact canonical `canonical_ud` plus `cue_axis`, where a unique non-corner border color-9 cue selects up/down versus left/right whole-grid reflection.
- Retained evidence: 31 focused tests, a 24-seed finite-rival audit (144 episodes / 1,104 labeled pairs), authoring preflight, protected-Racket wrong-axis witness, and one-query privacy checks.
- Limit: rival separation is finite, not a proof of universal uniqueness. Exact-source owner review, native qualification, acceptance, and any training admission remain pending.
- Next action: owner replays the retained source inventory and runs native acceptance without changing the canonical default.
