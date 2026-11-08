# Working notes: 04e2ffe8dc8e

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/04e2ffe8dc8e/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-26 full native build review

- **Base repair:** advanced the generator to `1.3.0`; made override handling fail closed and exactly observable, removed silent underproduction, consolidated `self_check`, and changed the ordinary three-slot schedule so every lesson contains a real non-green singleton that refutes the global-smallest-object shortcut.
- **Canonical preservation:** `workspace/parametric/canonical.rkt` is byte-identical to rule `c67640298f12` (`c67640298f129525479d507a5553f34126b3768c0acc153aabb0a03ff871c75d`).
- **Parametric setting:** `selection_mode=key_rank_green` measures the unique blue component (rank 2–4), then uses that input-dependent rank to select one of four size-ordered green components. Inputs are matched across settings, deterministic and count-independent; 2–6 demonstrations and four queries are supported, including a substantive 30×30 case.
- **Adversarial result:** the bounded probe passed 12 native jobs and 136 protected-Racket evaluations, varying the first two key ranks and refuting fixed-rank plus global-smallest-any-color bypasses. The wrong-rank protected counterfactual changes the selected component.
- **Retained evidence:** `workspace/parametric/evidence/manifest.json` (SHA-256 `ab27d788d6d5da560c355e8708af6d5b054625cce0f34d7de3e45faed65bcd88`), `checks/04e2ffe8dc8e/qualification/`, `checks/04e2ffe8dc8e/causal/`, `checks/04e2ffe8dc8e/first-turn.json`, and `checks/04e2ffe8dc8e-tests/result.json`.
- **Status/limit:** authoring preflight and causal replay passed; this is ready for owner source review. It is not owner-accepted and admits no training data.
