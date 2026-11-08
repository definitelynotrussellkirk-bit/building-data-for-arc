# Working notes: 027805c8ff0f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/027805c8ff0f/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-26 repair and native parametric build

Decision: preserve rule hash `2d205350180d` and the exact canonical default, repair the Python generator, then add the nearby `applications = once|twice` family. The base repair makes `shape_k` real, rejects unknown, invalid, or degenerate-incompatible overrides, reconciles advertised ranges, and strengthens the A→B transform self-check.

The parametric lesson infers an input-derived transform code from A→B and applies it to C once or twice. Inputs are independent of the setting, four query inputs remain stable across demonstration counts, and a 32-seed bounded census passed for 2 and 6 demonstrations (128 episodes, 1,024 labeled pairs, maximum 30×29). The protected-Racket authoring preflight, causal witness/replay, one-query export checks, and first-turn privacy checks all passed.

Current status: reviewer-ready only. Owner acceptance and training admission were not performed; the next useful action is exact-source integration followed by native owner qualification and fresh acceptance replay. Primary evidence is under `checks/027805c8ff0f/qualification/`, `checks/027805c8ff0f/causal/`, and `checks/027805c8ff0f/first-turn.json`.

## 2026-10-26 second audit

The second audit found that each fixed dimension profile encoded a fixed transform code, so a solver could infer Step A from grid size instead of A→B. Generation now uses seed-keyed shuffled blocks over transform codes 2–6 while preserving query-prefix independence and ensuring the first two demonstrations use different transforms. Randomizing the code exposed an axis-swapping 30×29 placement collapse; the sampler now distributes non-divider content across all four stress-grid quadrants.

Round-2 evidence: 75/75 combined focused tests, 31/31 isolated task tests, a 32-seed census covering every transform on every fixed profile, and a 128-seed adversarial sweep. The stress census observed minimum non-divider quadrant counts `[27, 20, 8, 11]`. Fresh source-bound preflight, witness, and public-projection evidence is generated under the round-2 check directories.
