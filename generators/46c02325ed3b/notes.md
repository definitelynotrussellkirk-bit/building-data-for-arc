## Current owner-accepted parametric family

The retained reviewed family is now accepted through `workspace/parametric/`.
`parametric/accepted.json` pins its exact current source and programs. The owner
rebased reviewer074 without replacing current production code; protected native
qualification covered both settings at seeds0/17, three demos and four queries,
and fresh owner acceptance replay passed. See `evidence/owner-prototype-rebase/`.
Canonical audits and training admission remain separate; earlier prototype
status below describes the source-bound reviewer handoff.

# Working notes: 46c02325ed3b

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric review — review-074a25e1be19297f

Built a proposed `spread_policy` family under `workspace/parametric/`. The
canonical `both` setting preserves the selected Racket program byte-for-byte;
`right_hand_only` retains gravity, wall collision and recursive flow while
keeping only the geometric right-hand branch at blocked fronts. Inputs are
matched across settings. Four retained queries cover top, bottom, left and right
sources at 10×10, 14×17, 18×18 and substantive 30×30 sizes.

Original reviewer-reported evidence covers both settings with three demonstrations and four
protected-Racket-labelled queries, demo counts 2–6, demo-only setting
certificates, public/private projection, rotations, atomic export and tamper
rejection. The bounded sampler pass exercised 60 episodes / 480 labelled pairs
across six seeds and all supported demo counts without a finding. Evidence is
bound by `workspace/parametric/evidence/reviewer-original/manifest.json`.

The existing task test was also made portable: it now resolves the canonical
ledger through `reviewer_support.find_root/canonical_path` instead of treating a
fixed parent depth as repository root. No production generator or rule semantics
changed. Current status is **prototype only**; the variant is not accepted or
training-admitted. The next useful action is independent semantic review and
explicit qualification/acceptance.
