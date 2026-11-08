# Working notes: 27a915a2c9b3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/27a915a2c9b3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-25 native parametric review

- Preserved the exact canonical halo program as the default.
- Added `halo_finish=largest_component_to_8`: run the canonical halo transform, then recolor the unique largest four-connected blue halo component to 8.
- The first teaching draft let a row-major-last shortcut survive because edge clipping repeatedly made the final component largest. The first two demonstrations now avoid clipping and alternate which component is largest; clipped and 30x30 boundary cases remain later in the bank.
- Added an executable skip-A counterfactual, bounded finite-rival audit, matched inputs across settings, stable query prefixes, four private queries, and a substantive 30x30 case.
- Repaired only the existing test's nonportable canonical-data lookup; the base generator and canonical labels were unchanged.
- Authoring preflight, protected causal replay, and public projection checks passed. This is reviewer-ready source, not owner acceptance or training admission.
