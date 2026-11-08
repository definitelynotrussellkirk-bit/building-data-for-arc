# Source-row parametric prototype

This source-bound prototype keeps the source task's copied first two rows and
background anchor at input cell `(2,1)`, while varying the visible row whose
background/non-background mask creates output row 2:

- `row0` is the exact canonical Racket program.
- `row1` derives the mask from the copied second row.

Inputs are identical across settings and deliberately give rows 0 and 1
different masks. A signal-colored distractor at `row1[1]` keeps the true
background anchor distinguishable. Episodes contain 2–6 demonstrations and
exactly four private queries, including a 30×30 ignored-context stress case;
both rules still emit exactly 3×width. All labels are replayed in Racket. This
prototype grants no production approval or training admission.
