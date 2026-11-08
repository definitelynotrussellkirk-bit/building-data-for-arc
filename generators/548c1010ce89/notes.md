# Working notes: 548c1010ce89

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/548c1010ce89/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-23 reconciliation: schedule contract and paint-color prototype

- Baseline: approved generator version `3.0.0`, source SHA-256 `e006dcd911c368137baa9767168002b5283c172912f57597158bf4152ac0317c`.
- Reconciled source: version `3.1.0`, source SHA-256 `baf9a05af0e287d52953d91261b6ea1d902e0fb50e583ca1acfe6a9ca21bce8d`.
- The three retained returns are duplicate evidence for one teaching defect, not competing rule changes: a default lesson can show only evidence compatible with a columns-only rule, then ask a query that also needs empty-row painting.
- Decision: repair the lesson schedule, not the canonical transformation. A four-slot cycle forces both-axis witnesses at slots 0 and 2 while broad slots preserve the full profile family. With `EXAMPLES_NEEDED = 3`, every three-of-four query rotation contains a demonstration that refutes both rows-only and columns-only competitors.
- The generator now declares executable semantic rivals, branch/witness predicates, and `lesson_identifiable`; explicit `scene_profile` overrides retain their prior behavior.
- Canonical authority is unchanged: normalized rule hash `506bc3722b18`, no canonical/base-solution edits, and the production paint color remains 2.
- Proposed extension: `workspace/parametric/prototype.py` selects `paint_color` from `{2, 6}` once per episode, uses three demonstrations plus four queries, executes selected and rival labels through exact Racket, retains the actual XORed input seed privately, and keeps hidden parameters/answers out of public bytes. Four retained episodes form two complete shared-input color pairs; report rows are public-ID sorted. It is not production-approved or training-admitted.
- Verification: 17 focused tests; complete declared schedule-period/rotation semantic gate (600/600 strict cases, 12/12 lessons, 0/48 ambiguous rotations); 3,072 additional bounded rotations; four Racket-backed adversarial prototype episodes; final protected-source/public-projection integrity check. No remaining observed failure in the changed scope.
- Owner action: replay the source-bound evidence, then resolve the three duplicate retained audits against the repaired source. Consider the paint-color extension independently; finite rival coverage does not establish uniqueness against arbitrary programs.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-8bbc1d0a8ab0ba4b:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e006dcd911c368137baa9767168002b5283c172912f57597158bf4152ac0317c`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit owner disposition after accepted reviewer repair review-319ab5f7ede14419: current repo/generators/548c1010ce89/generator.py SHA256 baf9a05af0e287d52953d91261b6ea1d902e0fb50e583ca1acfe6a9ca21bce8d. Reviewer-reported evidence: 17focused tests,600strict Racket semantic samples,12lessons/48query rotations and3,072additional rotations. Four-slot teaching schedule retains a both-axes witness after every query rotation, resolving all three duplicate seed727 columns-only reports. No owner battery rerun, universal identifiability or training admission. The audit on e006dcd911c368137baa9767168002b5283c172912f57597158bf4152ac0317c is resolved only for these repaired findings. Retained target-local evidence references: `checks/tickets/ticket-7fbbd238ec824ae4/audit_section.txt` `checks/tickets/ticket-7fbbd238ec824ae4/probe.py` `checks/tickets/ticket-7fbbd238ec824ae4/receipt.json` `checks/tickets/ticket-7fbbd238ec824ae4/run.json` `checks/tickets/ticket-7fbbd238ec824ae4/witness.json`

### Assessment or prior finding

## 548c1010ce89

**Independently confirmed existing teaching defect: the columns-only shortcut survives all three demonstrations.** Audited generator SHA-256 `e006dcd911c368137baa9767168002b5283c172912f57597158bf4152ac0317c`; executed canonical rule hash `506bc3722b18`.

The single bounded probe replayed the current audit's exact production-shaped witness: seed `727`, medium difficulty, sample indices `0..3`, no overrides, three demonstrations and one query. All four generated inputs pass the target's current `self_check`. Their profiles are `columns_only`, `columns_only`, `public_train_1`, and `rows_and_cols_sparse`.

The rival rule is: paint every entirely zero column red 2 and preserve all other cells. Real Racket authority outputs exactly match that rival on all three demonstrations. On the query (18 by 15; empty rows 10 and 14; empty columns 2 and 11), the authority also paints the empty rows, and the rival differs in 26 cells. The actual Racket outputs also match an independently written empty-row-or-column calculation for all four inputs.

This is confirmation of the already-retained source-bound finding, not a novel search result. The assignment seed `c3075deb6a883dee10346d388b6b71795a3e02e01ca158450f20e0160e568b62` identifies the ticket; reproduction seed `727` was selected from that same-source current audit. The three-demo schedule is permitted by the runtime's default demonstration policy; the peer declares no higher minimum.

Evidence: `checks/tickets/ticket-7fbbd238ec824ae4/witness.json` contains exact inputs, Racket outputs, rival outputs, validation results, source/rule hashes, and differing coordinates. `checks/tickets/ticket-7fbbd238ec824ae4/probe.py` reproduces the witness. `checks/tickets/ticket-7fbbd238ec824ae4/run.json` records the command, working directory, exit status and measured duration. Exactly one targeted probe ran, in 3.599 seconds including wrapper startup, within the 120-second bound. No peer source, rule, audit disposition, approval, or training admission was changed; no full battery or census was run.

Suggested maintainer action: ensure complete lessons demonstrate both empty-row and empty-column painting, or reject schedules where a single-axis rival remains consistent before the query. This focused replay supplies evidence for maintainer assessment and does not itself change review status.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-8bbc1d0a8ab0ba4b-v0001/audit_assets.json), manifest SHA-256 `8744060be3d560ed18ec4da40b22428ef787dd11b2c4d6ba5485779442306059`.
<!-- arcpuzzles-current-audit-assessment:end -->
