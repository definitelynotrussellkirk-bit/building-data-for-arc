# Working notes: 8b0844e3951e

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric design and implementation plan

Goal: preserve the exact canonical nonzero-mode fill and add one nearby,
episode-fixed `scope=global|modal_row` rule. In `modal_row`, compute the unique
global nonzero mode, select the unique row containing most of that color, then
fill with that row's unique most-frequent nonzero color other than the global
mode. The input-dependent row is necessary: redistributing cells without
changing any global color count can change the answer.

Architecture: a task-local Python sampler and exact Racket programs, a thin
native adapter/promotion contract, portable tests, and one rerunnable audit CLI.
The canonical production generator remains at its reviewed 3..5 dimensions.
The separate parametric input grammar extends to 3..30 for both settings;
the canonical Racket expression already supports those rectangular inputs.
Matched seeds use matched inputs so private settings do not select a visual
grammar. Both global and restricted modes and the selected row are strict.

The simpler runner-up-only variant was rejected because it collapses to a
single global ranking. A neighbor-halo variant was considered but the selected
row retains the original counting/fill reasoning with a simpler visible region.

Implementation checklist (spec: WORK/DUTIES.md, WORK/PARAMETRIC-RULES.md):

- [x] Add literal semantic, request-boundary and matched-input regression tests.
- [x] Implement `prototype.py`, native `adapter.py`, and `promotion.json`;
  support 2..6 demos and independent 1..4 query requests, normally 3/4.
- [x] Audit visible lessons against finite shortcuts, strict counts, private
  metadata projection and query-prefix stability; execute Racket labels at
  minimum and substantive 30x30 boundaries.
- [x] Build native source inventory and qualification, then a protected Racket
  wrong-row witness. Record actual results and acceptance-pending status.

Review focus: tied modes/row selectors; zero winning either comparison;
global-runner-up or fixed-row shortcuts; query/demonstration duplication;
hidden settings, answers or future queries leaking into the first turn.

### Current verification and handoff

Reviewer-ready, owner acceptance pending. The 49 focused tests pass. The
rerunnable `workspace/parametric/audit.py` checked 18 lessons against 22 finite
candidates, with 378 wrong-rival demonstration refutations and no wrong-query
survivors. Its 82 protected Racket evaluations cover both complete four-query
examples, six independently authored shortcuts and min/max count requests.
The saved public exports and private/future-field mutation checks pass; this
checks the first-turn projection, not a downstream query controller.

Native qualification passed for both settings at seeds 0 and 17, with three
demos and four queries each (40 protected evaluations). The native causal helper
constructed and replayed two wrong-row counterfactuals: 3x3 output color 2 versus
3, and 30x30 output color 8 versus 6. Main return evidence lives at
`checks/8b0844e3951e/qualification/`, `checks/8b0844e3951e/causal/`, and
`checks/8b0844e3951e/audit-final/`; the source inventory is task-local under
`workspace/parametric/evidence/manifest.json`. Independent review also exercised
65 seeds/requests without failure; see the compact source-bound review receipt.

The canonical generator still has SHA256
`dd29df3ec18cda8c98a1ba1f165a0b013e2e2f4519d4eb10750f528b283af5f2`.
No canonical rule or approval metadata was edited. Native acceptance must be
run after owner integration against the exact live source. These bounded checks
do not prove arbitrary-rule uniqueness, every-seed success, learning benefit,
or training admission. Optional peer findings do not change this family's gates.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/8b0844e3951e/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
