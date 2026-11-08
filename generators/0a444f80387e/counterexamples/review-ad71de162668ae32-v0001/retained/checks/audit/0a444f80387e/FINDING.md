## 0a444f80387e

**A2 — Reproduced teaching defect; findings only, no task-source changes.**
The production sampler can omit the demonstration needed to teach raw crop
semantics while asking a query that requires it. A plausible rival selects the
same qualifying component, then renders only that component on a zero background.
It fits all 5 labeled canonical pairs (4 train + 1 test), yet remains consistent
with every demonstration and predicts a different query in 8/100 tested medium
lessons. This is ambiguity in teaching, not a reference-label error.

Source binding: generator SHA-256
`9df826e90d3b82f23b1c1062500eb9db7e1c53bfa2afb92f6a7201b2c24e724c`;
executed canonical rule hash `6c2a8a51d8e3`; public apply rule-text SHA-256
`4eda4f3520204c665fb62f15abb7b4044f9dd7f47721be04488453b011add876`.
The authority-sync report separately records the selected canonical program's
exact SHA-256 as `6c2a8a51d8e3116a73b22feb2fb658c465ccf3abde4c956bfa94752843494f0b`.
These are different documented hash representations, not differing selected rules.

### Concrete generated witness

`checks/audit/0a444f80387e/ambiguous_lesson.json` retains the full production
lesson: seed **30**, difficulty **medium**, requested start **0**, accepted
sample indices **[0,1,2,3]**, three ordered demonstrations and one query, no
rejections and no overrides. This is generated support within the documented
helpful distribution, not a contrived validator-only input. All four inputs
reproduce exactly and pass the target `self_check` with no messages.

The rival matches all three demonstration labels. For query sample 3, the
selected color is 2; a foreign color-4 cell falls inside its larger component's
bounding box. Public Racket application produces
`[[4,2,0],[2,2,2],[2,2,0]]`; the rival produces
`[[0,2,0],[2,2,2],[2,2,0]]`. Thus output cell (0,0) distinguishes the rules,
but the preceding demonstrations did not provide that distinction.

The actual reference result, input, source hashes, command and effective working
directory are in `checks/audit/0a444f80387e/query_racket.json`. The rival result
and validator outcome are in `query_rival.json`; all four replay checks and exact
comparison with the production label are in `witness_verification.json`.
`rivals.py`, `probe.py`, and `verify_witness.py` are runnable retained tools.

### Scope and counts

The principal scan used public `Catalog.generate`, canonical Racket labeling,
medium difficulty, three demonstrations, one query, no overrides, starts at
sample index 0, and seeds **1–100 inclusive**. The 100 lessons contain **400
unique inputs** (accepted indices 0–3 per seed). Ambiguous lesson seeds are
**30, 31, 45, 71, 79, 82, 84, 99**. `probe_summary.json` records every episode's
seed, sample indices and rival agreement. No rotations, easy/hard bands, other
rivals, or exhaustive override space were tested. Consequently 8/100 is the
observed rate in this finite medium sample, not a distribution-wide estimate.

An initial 20-lesson scan at seeds 0–19 found 0 ambiguous lessons; its script,
summary and command log are retained as `probe_20.py`, `probe_summary_20.json`,
and `probe.log`. That scan overlaps the main scan at seeds 1–19, so the two
counts must not be added as independent evidence. There is no declared
`CANONICAL_SHORTCUTS` or `LESSON_COMPETITORS` contract to enumerate; the tested
rival is explicitly this audit's independent hypothesis.

### Authority and audit checks

The public `authority_sync` stage **passed**. Canonical and selected authority
are synchronized; both solve 4/4 canonical train and 1/1 canonical test pairs.
The retained archival raw source has different bytes but also solves all five;
this is reported as archival divergence, not a selected-authority defect.
Receipt: `authority-sync/checks/0a444f80387e_audit_authority_sync.json`.

The public `--stage audit --phase audit` preset completed both stages but
**failed**: task tests were absent (`no_tests`, exit 5), and the strict semantic
gate found no declared semantic contract (exit 2). The preset exit was 1.
Receipt: `stage-audit/checks/0a444f80387e_audit_summary.json`. Missing tests and
contracts are supporting verification gaps; they are not counted as passing.
An initial command used the nonexistent stage name `authority` and exited 2;
`authority.log` preserves that CLI mistake before the corrected successful run.

Recommended future repair: register the component-only rival and ensure each
production lesson supplies an intrusion witness before a query that depends on
raw crop semantics, either through a covered schedule or rival-aware lesson
rejection. Validate the resulting lesson assembly with source-bound tests and
query rotations when supported. No fix or training approval is supplied here.

Exact executable command arrays, launch CWDs, effective payload CWDs, exit codes,
and evidence paths are recorded in `checks/audit/0a444f80387e/COMMANDS.json`.
