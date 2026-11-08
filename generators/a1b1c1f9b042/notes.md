# Current notes

## Reconciled decision

Keep the semantic repair from both conflicted returns and the stronger structural contracts from the more complete return:

- preserve the unchanged canonical operation: stable left-packing per row;
- make order preservation observable in every default example with a shifted descending color pair;
- expose only real pixel-observable controls (`grid_h`, `grid_w`, `palette_size`);
- reject unknown, non-integer, out-of-range, and impossible overrides;
- retain strict input/scalar validation, exact canonical profiles, deterministic generation, semantic witnesses, and lesson competitors.

Do not restore the old inert controls (`palette_kind`, `anchor_corner`, `asymmetry_force`, `position_bias`, `n_distinct_colors`, or degenerate `texture` aliases). They did not provide truthful controllable variation.

## Shortcut answer

The strongest plausible shortcut was: **sort each row’s nonzero colors ascending, then pack them left**. It fit the retained old three-demonstration window (`seed=21`, `difficulty=easy`, indices 0–2). The fourth old sample defeated it because the correct bottom-row sequence is `[8,5]`, while sorting predicts `[5,8]`.

A current concrete query is:

```json
[[0,9,0,1,0,4],
 [3,0,6,0,0,5],
 [8,0,0,0,0,2]]
```

Canonical stable packing returns:

```json
[[9,1,4,0,0,0],
 [3,6,5,0,0,0],
 [8,2,0,0,0,0]]
```

The shortcut instead predicts:

```json
[[1,4,9,0,0,0],
 [3,5,6,0,0,0],
 [2,8,0,0,0,0]]
```

The repaired generator puts a maximum-then-minimum pair on a shifted first row, so ascending sorting is wrong in every default demonstration rather than merely in a held-out query.

## Corrected profile interpretation

An early reconciliation draft treated a native profile coordinate as occupied-cell count. The profile gate showed that coordinate is distinct colors including background. The final canonical branches therefore use:

- `3×6`: 7 or 8 nonzero colors, 7 or 8 occupied cells, hence 8 or 9 distinct colors including background;
- `4×5`: 9 nonzero colors and 9 occupied cells, hence 10 distinct colors including background.

## Evidence and next action

- Focused tests: `checks/task-tests-package-final/result.json` (70/70).
- Native source-bound gates: `checks/*-source-final/result.json` (11/11).
- Independent probe: `checks/reconcile-probe-final/report.json` (108/108 Racket parity; 864 rotations).
- Production-format 3-demo/4-query episode: `checks/four-query-final.jsonl`.

No canonical rule change, approval, or training admission is requested. The next useful action is a bounded model-in-the-loop comparison of old versus repaired lessons under matched accepted-token budgets; source/Racket parity does not need another broad rerun unless source bytes change.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4c10bb8a426de6a4:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0e428507c3c2a7f12d1e68e9e29e80a9b853f2c0c08fb793589bec0457a5ba3b`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit owner disposition after accepted reviewer repair review-dc9c3e47ef4a0470: current repo/generators/a1b1c1f9b042/generator.py SHA256 16818c29bb8fb21e91ee5bb6abdd4f56158cfdd468d1422f619d75835e7a9ed2. Reviewer-reported evidence: 70focused tests,108Racket parity cases,864rotations and honest controls/domain checks. Each ordinary input contains a shifted descending pair, forcing order preservation and refuting ascending sort. No owner battery rerun, universal identifiability or training admission. The audit on 0e428507c3c2a7f12d1e68e9e29e80a9b853f2c0c08fb793589bec0457a5ba3b is resolved only for these repaired findings. Retained target-local evidence references: `checks/audit/a1b1c1f9b042/apply.log` `checks/audit/a1b1c1f9b042/generation.json` `checks/audit/a1b1c1f9b042/input.json` `checks/audit/a1b1c1f9b042/racket.json` `checks/audit/a1b1c1f9b042/witness.json`

### Assessment or prior finding

## a1b1c1f9b042

**Finding A1 — a three-demonstration sorting shortcut remains plausible.** Audited generator SHA-256 `0e428507c3c2a7f12d1e68e9e29e80a9b853f2c0c08fb793589bec0457a5ba3`; rule hash `8cd149b15ecf`.

For `seed=21`, `difficulty=easy`, generated sample indices 0, 1, and 2 are all lawful (`self_check=[]`) and their Racket labels also match this rival: within each row, sort the nonzero values ascending, then pack them against the left edge. The rival therefore fits those three consecutive possible demonstrations. Sample index 3 is a concrete distinguisher: its bottom row must preserve `[8,5]`, while the rival predicts `[5,8]`.

The exact four inputs, intended outputs, rival outputs, hashes, generation coordinates, and Racket binding are in `checks/audit/a1b1c1f9b042/witness.json`. The authority receipt is `checks/audit/a1b1c1f9b042/racket.json`; its rule hash matches the catalog. This is a concrete three-example ambiguity witness, not a census of every assembled lesson, so I am not claiming every production lesson is defective.

**Disposition:** actionable teaching-risk evidence; audit target left unchanged as required.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4c10bb8a426de6a4-v0001/audit_assets.json), manifest SHA-256 `fc266f7bb95a1fe1d6fdafc0404561aaa1fc8291a16f1429238ce5ecd3345fa7`.
<!-- arcpuzzles-current-audit-assessment:end -->
