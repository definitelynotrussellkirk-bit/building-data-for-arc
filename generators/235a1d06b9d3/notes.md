# Working notes: 235a1d06b9d3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/235a1d06b9d3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 repair and parametric handoff `review-2f669e754965367d`

Built `workspace/parametric/source_row_episodes.py` with one episode-fixed
parameter, `source_row`:

- `row0` is the exact canonical Racket program and remains the default.
- `row1` preserves the copied first two rows and background anchor but derives
  output row 2 from the second visible row's mask.

Inputs are identical across settings and deliberately give rows 0 and 1
different masks.  The adapter supports 2–6 demonstrations and exactly four
private queries, including a 30x30 ignored-context case whose output remains
3x30.  Focused tests replay both programs in Racket and cover demo-only
identifiability, public/private projection, sequential turns, public IDs, batch
binding, and corrupted-label rejection.

A production-domain defect was also repaired.  Every previous generated input
had `input[1][1] == input[2][1]`, so a wrong program reading the background from
row 1 fit the entire generated domain and all five canonical pairs.  Version
3.1.0 keeps all five public morphologies unchanged while general profiles place
a controlled signal decoy at row 1, column 1.  The shortcut, witness, and exact
discriminator are now executable regressions.  Retained tests were also made
source-bound for portable runtimes.

Native promotion qualification correctly stops at the current-source approval
gate because the production generator hash changed in this repair.  Owner
review/re-approval is the next step; no authority rule changed, no gate was
bypassed, and no variant acceptance was attempted.
