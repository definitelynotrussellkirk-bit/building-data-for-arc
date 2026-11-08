# Working notes: 6237039401ed

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Confirmed sampler coverage gap: the “recolor four-connected gray components with at least4cells” rival fits all8demonstrations and all5storedqueries in two exact current-source lessons. The grammar only contrasts solid rectangles with smaller distractors. A fresh canonical Racket witness containing a T-tetromino plus a solid2×2 target separates the rules at4cells; that T is outside the current sampler grammar. Add a non-square size>=4 negative teaching component while preserving overlapping-window positives.

Exact lessons, source hashes and executable-reference evidence: `evidence/trainer-ambiguity-current/current.json` and `coverage-check.json`. This is an open teaching issue, not evidence of wrong stored labels. No production repair, approval change, training exclusion or audit closure is claimed.
<!-- arcpuzzles-trainer-ambiguity:end -->

## Accepted complete-window parameter family

The separate native family at `workspace/parametric/` is accepted on exact
source: window side2or3 and minimum per-cell overlap1or2 (four settings).
Detect all complete windows in the original scene, count their cell memberships,
then repaint. Protected Racket counterfactuals show why painting during detection
changes later eligibility. The default preserves the canonical Racket bytes.

Two common demonstrations include large negative T/ring components, an ineligible
positive tail, and unequal overlapping cores. Independent review found a
largest-rectangle shortcut in the first attempt; the mandatory unequal-core
contrast now rejects both crop-to-core and mask-to-core alternatives for all
four settings. Inputs match across settings and preserve independent2–6demo and
1–4query prefixes; query sizes are permuted by a separate seed stream. Normal
use has2demos/fourqueries and a substantial30×30query without a fixed query slot.

Exact acceptance and verification scope: `evidence/owner-window-membership/current.json`.
This richer native grammar does not repair or close the unchanged canonical
sampler coverage audit above, and does not admit model trajectories to training.
