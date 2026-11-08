# Working notes: 5f6fdf4f9900

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/5f6fdf4f9900/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current native parametric work

`workspace/parametric/adapter.py` implements `corner_priority=scan|largest_component`.
The default returns the exact canonical program; the alternative compares the
same-color four-connected areas of eligible diagonal neighbors before choosing
which red diagonal to paint. Ties preserve NW, NE, SW, SE. The separate grammar
admits disconnected same-color regions and inputs up to 15×15 when the enlarged
output fits 30×30. The canonical generator and selected rule remain unchanged.

Support is 2–6 demonstrations and 1–4 independent novel queries, ordinarily
3 demos/4 queries. Input draws match across settings. Two constructive demos
cover scales three/four, competing orientations, size ties, blocked larger
neighbors, disconnected colors and four-versus-eight connectivity.

A protected-Racket self-audit found that smallest-component selection fit the
initial scan demonstrations but changed a seed-17 query. Moving the isolated
fourth-color cell in the second demo from (4,5) to (5,3) rejects that shortcut
without adding demonstrations. The original lesson and both executable answers
are retained in `checks/5f6fdf4f9900/teaching-repair-witness.json`; it is suitable
as a candidate alternative-answer case, not a second official gold label. The
repaired core is unambiguous within the ten tested rivals. The final finite
audit, private labels and safe one-query projections are in
`checks/5f6fdf4f9900/self-audit/`.

Native qualification passed for both settings at seeds 0/17 with 3 demos and
4 queries, including populated 30×30 outputs. See
`checks/5f6fdf4f9900/qualification/qualification.json` and sibling `execution.json`.
The source inventory is `workspace/parametric/evidence/manifest.json`.
`checks/5f6fdf4f9900/causal/witness.json` binds the area-comparison dependency
to a protected-Racket skip-A counterfactual. Qualification is reviewer evidence;
the owner must qualify and accept the exact integrated source before native use.
No training admission is claimed.

The legacy test loader now uses the same-checkout `reviewer_support` helpers;
direct and isolated/relocated tests execute. The inherited exact-string test
still fails because raw/base target texts differ from the canonical text in
formatting. Its assertions were retained. Both distinct programs matched all
four public pairs (8 protected-Racket evaluations), which does not resolve the
active exact-source synchronization requirement. The old missing canonical
lesson contract and composite audit remain open; this separate parameterized
family does not clear them. See `checks/5f6fdf4f9900/portable-test-authority-parity.json`
and `portable-test-relocation.json` for the bounded evidence.
