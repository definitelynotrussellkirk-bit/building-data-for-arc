# Public parent b0039139 — authoring design

The four panels are separated by exactly three full blue lines. The first
contains a yellow template, the second contains green 4-connected markers,
and the final two specify foreground and background colors. Crop the template,
map its colors, and repeat it once per marker component along the panel-layout
axis, inserting one background row/column between copies. This hypothesis must
match all four supplied demonstrations and both private test golds.

The default is preserved exactly in reference.rkt. The alternative
`area_parity_relay` extracts the ordered green components and reflects a copy
along the repetition axis exactly when its corresponding component has odd area.
This uses component identity and geometry, not a global cell count or raw row
count. Canonical and alternative share input streams. No lookup labels are used.

The native adapter supports 2–6 demos and 1–4 queries. All four queries are built
before a seed-keyed independent presentation shuffle and prefix selection.
Settings, source indices, programs, and test answers stay private. The 30×30
case has a full-height template, distributed markers and full palette panels.

Implementation plan:
- [x] Pin all original labels and API/privacy/teaching invariants in failing tests.
- [x] Implement canonical Python mirror, independent Racket rule and sampler.
- [x] Add relay, exact-path adapter, wrong-intermediate program and contract.
- [x] Audit finite rivals, execute original/generated labels, exports and causal case.
- [x] Run unapproved authoring preflight; package source-bound evidence.

Review focus: horizontal/vertical layouts; multi-cell versus singleton markers;
asymmetric crops and internal zero cells; same colors reused by palette panels;
30-cell input/output bounds; deterministic independent demo/query counts;
invalid exact-integer cells; private-field invariance.

Not owner-registered, qualified, accepted, or admitted to training.

## Current executed evidence

All six official labels (four train, two private test) match protected Racket.
74 task tests pass. The 64-seed, 2-mode, 2/3/6-demo audit covers 384 episodes and
3,840 named-rival checks with no retained failure, plus 82 protected evaluations.
The independent replay changes 124 cells in the 30×30 causal case. All 16 public
views pass structure/hash checks; 20 hidden-field mutations leave visible bytes
unchanged. Six deliberately malformed exports are rejected.

Use `workspace/parametric/verify.py --preflight PATH --out NEW --seeds 64`
through this checkout's Racket-enabled environment. It checks exact source hashes,
refuses stale preflights, audits named rivals, exports one query at a time, and
replays the source-bound counterfactual. A finite check does not prove uniqueness.

The new public task is not yet in the owner catalog, so the staged `task-tests`
command reports Unknown puzzle; direct pytest with `--import-mode=importlib`
is the working authoring path. Owner registration, native qualification and
acceptance remain pending. The preflight is explicitly not qualification.

## Current private repeated-parent reconciliation

No semantic merge: same canonical/area_parity_relay programs and same sampler. Adopt incoming adjacent canonical resource and explicit manifest resources with focused tests. Retain current standalone generator metadata byte-exact. Candidate native qualification and fresh acceptance were exercised in this isolated library; root publication remains separate. See evidence/repeat-next-union and the current private qualification receipt.
