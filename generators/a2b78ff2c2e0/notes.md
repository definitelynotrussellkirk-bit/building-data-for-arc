# Working notes: a2b78ff2c2e0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a2b78ff2c2e0/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-25 native parametric family review

- Kept the canonical row-major serialization program and base generator unchanged.
- Added `workspace/parametric/` with exact `scan_only` default and sequential `scan_then_rle` setting.
- Fixed the observed histogram shortcut by repeating a color in separated runs in every scene.
- Final evidence: 26 task tests; 256-seed/5,120-pair audit with no declared rival survivor; protected authoring preflight; reversed-intermediate causal replay; 16 verified public views.
- The shared preflight's single-pair split bug is retained as compatibility evidence, but no shared source edit is returned.
- Current status is reviewer `prototype / ready`. Owner source review, fresh qualification/acceptance, and training admission are still required.

