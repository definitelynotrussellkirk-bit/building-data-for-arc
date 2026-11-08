# Review review-5fa97edbba52e932 — two new public families

Both task sources are version 1.0.0; no prior canonical references existed.
221dfab4: border-stripe inference; `extension=slice|component`; all 4 official labels pass.
c4d067a0: infer miniature-to-square registration; `completion=all|anchored_components`; all 4 official labels pass.
Full final task tests: **33 + 36 = 69 passed**, with exit-0 per-task receipts.
Final audits: **120 episodes, 920 pair claims, 120 protected Racket evaluations, 1,200 rival checks, 48 public views**, zero findings.
Both exact-source authoring preflights and protected causal replays pass; each ablation changes 36 cells.
Repaired generator relocation: workspace imports removed from ordinary generator entry points.
**Needs owner attention:** unchanged shared runtime rejects the required `public_eval_...` IDs.
A narrow, unapplied owner patch passes 22 guard tests and both normal base-generation replays in a disposable copy.
**Not owner-qualified/accepted; training admission false.** Source review is author self-review, not independent review.

## Delivered behavior

The stripe rule obtains its direction and band from a yellow boundary segment,
projects alternating stripes, and extends every third stripe onto foreground.
The alternate first intersects original same-color four-connected components
with the inferred green stripes, then recolors entire selected objects. Untouched
same-color and diagonal-only-contact objects defeat color-global/8-connected
shortcuts. The wrong component-hit intermediate changes the 30x30 result.

The enlargement rule infers a miniature lattice, enlarged block size, target
pitch and unique alignment from repeated-color seed squares. It completes the
full pattern, or only the color-agnostic four-connected template components
containing registered seeds. The final 30x30 scene touches bottom/right boundaries.
A wrong inferred target origin changes its final rendering.

Both adapters support independently chosen 2..6 demos and 1..4 requested queries
while always retaining four private distinct queries. Inputs match across
settings. Controller presentation is shuffled independently and whitelisted
public views contain only demonstrations and one current input. The 10-rival
audit per family is finite and does not prove universal uniqueness or efficacy.

## Evidence / integration

Authoritative current evidence is under each `checks/TASK/{audit-final,preflight-final,causal-final}`
and `final-tests.log`. Original labels include every supplied test gold.
`RESULTS.json` binds source hashes, paths, commands and failures.
`checks/OWNER_RUNTIME_BLOCKER.md` gives the exact native admission failure,
minimal proposed shared patch, copy-only reproduction and required evidence refresh.
Original catalog, canonical ledger, public parents and shared runtime remain unchanged.

The earlier catalog-backed task-test wrapper could not resolve unregistered
identities. The combined direct run printed all passes but lost its outer launcher
receipt; separate complete task runs succeeded and carry exact exit-0 receipts.
No unrelated repository-wide suite, training run, or native owner acceptance is
claimed. The reusable task-local audit tools, strict regression suites, pure
public projections and isolated registration/ID-guard tools are included.
