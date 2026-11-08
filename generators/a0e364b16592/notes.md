# Working notes: a0e364b16592

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a0e364b16592/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current review decision — 2026-10-25

- Repaired the production sampler because its ordinary lessons omitted color-5 blockers, allowing a global-bottom shortcut to match generated inputs. Ordinary draws now include a fixed blocker with payload above and below it, and `self_check` enforces the observable segment distinction.
- Added a native two-setting family under `workspace/parametric/`: exact canonical `canonical_down` plus `cue_side`, where a unique top/bottom color-9 cue determines gravity direction while colors 5 and 9 remain fixed.
- Retained evidence: 31 focused tests, a 24-seed finite-rival audit (144 episodes / 1,104 labeled pairs), authoring preflight, protected-Racket wrong-direction witness, and one-query privacy checks.
- Limit: rival separation is finite, not a proof of universal uniqueness. Exact-source owner review, native qualification, acceptance, and any training admission remain pending.
- Next action: owner replays the retained source inventory and runs native acceptance without changing the canonical default.
