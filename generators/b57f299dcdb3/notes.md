# Working notes: b57f299dcdb3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/b57f299dcdb3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current parametric design — review-c580b6d6a339f943

The new opt-in `workspace/parametric/` family uses `readout=winner_color|winner_pluses`.
The scalar default is the exact selected canonical program; the alternative
uses the inferred plus-census winner to retain complete winning objects on a
zero canvas. A two-demo intervention flips one plus color, changes the winner,
and changes mask membership of untouched objects. This is an input-dependent
census → winning color → object-selection dependency, not iterative simulation.

Matched input streams support 2–6 demonstrations (normally 3) and 1–4 queries
(normally 4). The first two demonstrations refute fixed color/position/first-repeat
choices; noise, invalid yellow crosses and non-yellow-centered crosses challenge
loose detection and global frequency. Queries vary repeated-color multiplicities
and geometry through substantive 30×30 input/output support. This expanded
prototype grammar is separate from production's 20–27 by 22–24 strict domain;
no production size override or default-distribution change is claimed.

The legacy task test now uses portable same-tree loading. This exposes the
pre-existing `test_base_sources_match_canonical_program` failure: both training
and augmented base `raw_code`/`target_code` retain legacy text differing from the
selected canonical ledger. The equality assertions and protected base sources
remain unchanged; evidence is `checks/b57f299dcdb3/portability/summary.json`.
The inventory and qualification below bind the canonical ledger exactly.

Current scope and limits: production generator and rule are unchanged, so the
older production-distribution global-frequency audits remain unresolved. New
finite-rival evidence applies only to the opt-in family. Owner integration,
fresh native qualification and exact-source acceptance remain the next action;
no training admission or activation is implied. See `workspace/parametric/README.md`
for runnable commands and the final review's source-bound evidence paths.
