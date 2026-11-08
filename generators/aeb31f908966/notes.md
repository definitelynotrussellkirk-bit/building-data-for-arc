# Current account: aeb31f908966

## Intended rule

A single color-2 marker selects a reflection axis. A marker on row 0 selects its column; a marker on column 0 selects its row. For each color-5 source cell, compute the mirror position across that axis and paint color 7 only when the target is in bounds and currently 0. Existing nonzero cells and out-of-bounds targets are unchanged. The selected authority is pinned by `RULE_HASH = "efb0a4280598"`.

## Decisions in version 4.0.0

The previous 3.0.1 sampler put ordinary gray sources on only one side of its axis, exposed controls that were not exact or observable, did not declare executable semantic rivals, and supplied weak canonical profile support. It has been replaced with a deterministic six-profile curriculum. Every six consecutive generated pairs include top and left markers, negative- and positive-side sources, two occupied-target cases, and two out-of-bounds cases. The public axes are now limited to six exact, constructive, recoverable controls: `grid_h`, `grid_w`, `orientation`, `shape_side`, `n_5cells`, and `edge_case`.

Five demonstrations plus one query form the intended lesson. `LESSON_SCHEDULE_PERIOD = 6`; every cyclic start and every held-out query rotation is checked by task-local tests. Named competitors include overwrite-on-occupied, modulo-wrap out of bounds, one-sided-only, one-orientation-only, and identity rules. The two strongest canonical-fitting shortcuts are retained in `CANONICAL_SHORTCUTS` with minimal counterexamples under `counterexamples/`.

`workspace/reference_probe.py` is an independent Python oracle and rival/witness toolkit for future reviewers. It does not call the generator's internal solver. Focused tests compare all five canonical labels with this oracle and verify exact override observability, malformed-input rejection, cyclic schedule coverage, shortcut witnesses, and rotated-query identifiability.

The selected Racket `target_code` was synchronized byte-for-byte with the canonical program by removing two generic comments only. The executable rule did not change; archival `raw_code` is unchanged. Proposal/evidence: `checks/authority-sync-proposal.json`.

## Evidence

- Final generator SHA-256: `89305432557d22d7a73d4ccceb6ba65edb3c396cae08d7a806abc7fafcf130b4`.
- Before battery: 6 green, 2 advisory, 4 failed (`checks/before/checks/aeb31f908966_before_battery_summary.json`).
- Final after battery: 12/12 green, including strict rotations and fixed-seed enumeration of all six schedule residues (`checks/after/checks/aeb31f908966_after_battery_summary.json`).
- Portable focused regressions: 67 passed (`checks/task-tests/`).
- Production lesson census: 300 lessons, 1,800 labeled pairs, 1,800 query rotations, 0 ambiguous production lessons, 0 ambiguous rotations, 1,648 unique inputs (`checks/lesson-census.summary.json`).

## Assumptions and limits

The semantic checks cover seven explicitly named rivals plus the census's generic searched rivals; they are not a proof against every conceivable hypothesis. The 300-lesson census samples production starts and rotates each six-pair bundle, but it does not exhaust all seeds. Task-local tests exhaust all six start residues over multiple seeds and bands. `shape_side` describes the majority/source construction side; an occupied-target profile intentionally contains a mirrored color-5 cell on the opposite side. Generated sizes are 10..16, while the schedule itself stays on the four canonical height/width profiles so each difficulty band meets exact profile support.

No open blocker remains for this repair. Training admission and catalog approval remain maintainer-owned.
## Current reviewer considerations

Source SHA-256: `89305432557d22d7a73d4ccceb6ba65edb3c396cae08d7a806abc7fafcf130b4`.

# Decisions — aeb31f908966

## D1 — Preserve the canonical rule; repair the generator and textual authority binding

**Decision.** Keep the canonical semantics unchanged: the marker selects the axis, and color 7 is added only at in-bounds background mirror targets. Pin `RULE_HASH = "efb0a4280598"`.

**Reason.** All five canonical labels and the selected Racket implementation agree. The baseline defects were in sampling, metadata, validation, teaching coverage, and exact-text authority synchronization—not in the transformation itself.

**Alternative rejected.** Overwrite occupied targets or wrap out-of-bounds targets. Both alternatives fit all five canonical demonstrations, so they are retained as explicit rivals, not adopted as the rule.

**Probe/evidence.** `workspace/reference_probe.py`, all canonical-pair focused tests, `checks/question/occupied-racket.json`, and final rule-smoke/semantic stages.

**Failure mode/limit.** The canonical demonstrations alone do not distinguish the two retained shortcuts; generated lessons must do so.

## D2 — Replace the former free/random sampler with a period-six semantic curriculum

**Prior choice.** Version 3.0.1 randomized orientation/size but ordinary source placement was effectively one-sided and did not guarantee occupied or out-of-bounds witnesses.

**New choice.** Use six deterministic semantic profiles:

1. top / negative / clean / 11×11;
2. top / positive / occupied / 10×12;
3. left / negative / clean / 12×10;
4. left / positive / occupied / 12×12;
5. top / negative / out-of-bounds / 11×11;
6. left / positive / out-of-bounds / 12×12.

Within a profile, seed-derived RNG still varies axis placement and shape geometry. Every consecutive six pairs supply the complete teaching set.

**Reason.** The curriculum makes semantic support falsifiable and cheap to enumerate. It directly addresses both canonical-fitting shortcuts and the baseline one-side restriction while guaranteeing canonical-profile support in every difficulty band.

**Alternatives rejected.**

- Pure independent random draws: easier to write, but lessons could omit rare occupied/OOB witnesses or one orientation.
- A larger period: unnecessary; six pairs exactly match five demonstrations plus one query and cover all required branches.
- Only canonical layouts: too narrow; geometry and axis positions should still vary.

**Probe/evidence.** `LESSON_SCHEDULE_PERIOD = 6`; cyclic-start and held-out-rotation tests; final enumerated semantic battery; 300-lesson census.

**Failure mode/limit.** A deterministic schedule is itself learnable metadata. Query rotations, multiple seeds, and varying geometry reduce but do not eliminate every schedule-aware shortcut.

## D3 — Keep four canonical size/color profiles, but retain legal exact size overrides

**Decision.** Scheduled defaults use 11×11, 10×12, 12×10, and 12×12, all with colors {0,2,5}; exact overrides may request any 10..16 height/width.

**Reason.** Exact scheduled profiles make each easy/medium/hard band satisfy the strict profile floor. The wider override domain preserves controlled stress testing without weakening production support.

**Alternatives rejected.**

- Difficulty-specific random size bands: baseline evidence showed weak canonical support, especially medium/hard.
- Restrict all legal sizes to canonical dimensions: unnecessarily limits controlled tests and geometry variation.

**Probe/evidence.** `checks/after/checks/aeb31f908966_after_profile_floor.json` reports 20/20 exact hits per band; focused overrides cover minima, maxima, and mixed dimensions.

**Failure mode/limit.** Production defaults do not sample every legal overridden size. The public contract is nevertheless exact and tested for all endpoints and combinations by the override gate.

## D4 — Expose only observable semantic controls

**Decision.** Public `AXES` contains exactly `grid_h`, `grid_w`, `orientation`, `shape_side`, `n_5cells`, and `edge_case`. Unknown keys and malformed values fail loudly.

**Reason.** Each control is constructive and recoverable from the returned grid. This prevents metadata-only axes and silent ignored requests.

**Alternative rejected.** Retain legacy axes or diagnostic toggles that do not change a grid. Such controls should be internal or explicitly diagnostic, not advertised as exact generation controls.

**Probe/evidence.** `observe_overrides`; focused exact-override tests; final override stage (PASS with no findings).

**Failure mode/limit.** `shape_side` names the primary/majority construction side. Occupied profiles deliberately add a mirrored gray cell on the opposite side; this is documented and the observer uses the intended majority semantics.

## D5 — Treat occupied and out-of-bounds behavior as first-class lesson branches

**Decision.** Emit two `occupied` and two `out_of_bounds` profiles per six-pair schedule, not merely rare random cases.

**Reason.** The strongest canonical-fitting shortcuts differ only on those branches. Without both, correct labels can still form an ambiguous lesson.

**Alternatives rejected.**

- Only clean mirrors: maximizes visual simplicity but leaves the intended guard conditions unteachable.
- A single edge-case example: unsafe under arbitrary held-out query rotation; the sole witness could become the query.

**Probe/evidence.** `counterexamples/occupied-target.json`, `counterexamples/out-of-bounds-wrap.json`, schedule witness tests, and `checks/lesson-census.summary.json`.

**Failure mode/limit.** Other plausible edge semantics may exist; the retained rival list is finite.

## D6 — Require at least one productive mirror and reject malformed semantic inputs

**Decision.** `self_check` validates rectangular ARC grids, legal colors, exactly one non-corner edge marker, 3..8 gray cells, no gray cell on the selected axis, and at least one in-bounds empty mirror target.

**Reason.** A grid with no productive reflection teaches identity rather than the intended operation. Strong validation prevents malformed or semantically inert examples from reaching Racket.

**Alternatives rejected.** Accept all syntactically colored grids and rely on the authority. That permits no-op examples and hides generator defects until labeling time.

**Probe/evidence.** destructive-mutation tests and final selfcheck/defect-lint stages.

**Failure mode/limit.** Validation establishes domain lawfulness, not lesson uniqueness; semantic rivals are checked separately.

## D7 — Build an independent oracle and retain failing-first evidence

**Decision.** Put an independent rule/rival implementation in `workspace/reference_probe.py`, with focused portable tests under `tests/`. Retain both the failing baseline test log and passing final log.

**Reason.** Tests that call production helpers can reproduce the same bug. The independent probe gives future agents a small, reusable, source-bound way to compare canonical labels, generated grids, observers, and rivals.

**Alternative rejected.** Test only generator-private `_rule_output`. That would not independently validate the algorithm or metadata observer.

**Probe/evidence.** `checks/tdd-red.log` (63 failed, 4 passed against the baseline), `checks/tdd-green-attempt1.log` (67 passed), and portable `checks/task-tests/` (67 passed).

**Failure mode/limit.** Python and Racket implementations could share a conceptual mistake. Canonical pairs and direct public Racket execution provide an additional independent binding.

## D8 — Synchronize selected authority text without changing behavior

**Decision.** Apply the generated selected-authority proposal that removes two generic comments from `racket_target.target_code`, making it exactly match canonical program text. Preserve archival `raw_code`.

**Reason.** The baseline authority-sync stage failed solely on exact text. Execution parity already passed, and the proposal changed no tokens with semantic effect.

**Alternative rejected.** Leave comment-only divergence unresolved. That would keep the strict battery red and obscure future real authority drift.

**Probe/evidence.** `checks/authority-sync-proposal.json`; source file changed from SHA-256 `9f210a...` to `b0b523...`; final authority-sync and rule-smoke stages pass.

**Failure mode/limit.** Exact textual equality is a provenance guarantee, not a general proof of semantic equivalence.

## D9 — Use five demonstrations and require arbitrary single-query rotations

**Decision.** Set `EXAMPLES_NEEDED = 5`; lessons contain six consecutive pairs, one used as query. Require every one of the six possible held-out positions to remain identifiable against named rivals.

**Reason.** With one witness per semantic branch, arbitrary rotation could hide the only refutation. The duplicated occupied/OOB coverage and the full six-profile set make every rotation robust.

**Alternatives rejected.**

- Three demonstrations: too easy to omit one orientation, one side, or an edge guard.
- Ordered-query-only validation: insufficient when downstream assembly may rotate queries.

**Probe/evidence.** Task-local exhaustive cyclic-start/rotation tests; final semantic battery with `--require-rotations-identifiable`; census with `--rotate-query`.

**Failure mode/limit.** The census samples 100 lesson starts per band and rotates each bundle; task tests enumerate all six residues across multiple seeds. Neither is a proof over infinite seeds and arbitrary undeclared rivals.

## D10 — Preserve audit targets as findings-only

**Decision.** Do not modify `374fae0ec7a2` or `c7a8e8d171fa`.

**Reason.** Assignment audits are adversarial inspection, not repair authorization.

**Evidence.** `AUDIT.md` and `checks/audit/`. `374fae0ec7a2` passed its full battery; `c7a8e8d171fa` has a separately reproduced advertised-control defect and six failing stages.
