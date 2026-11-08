# Working notes: 8862a204ce3a

## Intended rule and authority

A nonzero cell in column 0 is a row header. The output replaces that entire row with the header color. A row whose column-0 cell is zero becomes entirely zero. The canonical Racket program remains authoritative and is pinned by `RULE_HASH = "067caed98cc7"`; `rule_mirror` is test/diagnostic code only.

## Current generator design (v3.0.0)

- Five `canonical_*` scene profiles exactly reproduce the canonical `(height, width, marker-count)` signatures; five disjoint `broad_*` profiles widen support inside the observed envelope.
- Headers use two or three distinct nonzero colors. `row_layout` controls whether top/bottom boundary rows are marked.
- The default schedule alternates `canonical` and `contrast`. Clean canonical items contain only first-column headers.
- Every contrast item contains both zero-header noise and a conflicting colored cell in a marked row, using only existing header colors.
- `EXAMPLES_NEEDED = 3`; therefore every consecutive three-demo window contains a contrast item that refutes both declared shortcuts.
- Public exact controls are only `scene_profile` and `row_layout`, and `observe_overrides` recovers both from pixels.

## Reversed prior decisions

The imported v2.0.1 sampler always created three fixed-position headers and two fourth-color decoys. That produced five nonzero objects/four colors even though canonical inputs have two or three headers and two or three nonzero colors, and it made several advertised axes inert. v3.0.0 replaces that fixed grammar with observable profile/layout controls and uses relation-based controls rather than a dedicated decoy color. Evidence: baseline lint/self-check/defect failures under `checks/before/`; final 12/12 battery under `checks/after-final-3/`.

The first v3 draft also left difficulty bands byte-identical. The final version applies a band-specific profile offset while leaving lesson semantics and exact override support unchanged. The failed intermediate detector is retained at `checks/after-final/checks/8862a204ce3a_after_defect_lint.log`.

## Validation and teaching contract

`self_check` owns the finite training domain: rectangular integer colors, a declared profile signature, exact/distinct headers, no undeclared colors, no repeated header color outside column 0, and at most three controls of each type. `strict_canonical_like` requires one of the five exact source signatures and no off-header nonzero cells.

Canonical examples admit two concrete wrong rules:

1. fill marked rows but preserve contents of zero-header rows;
2. fill only blank cells in marked rows, preserving conflicts.

They are executable in `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`, with matching witnesses and a `lesson_identifiable` hook. The minimal retained input `counterexamples/overwrite_and_clear.json` refutes both and is covered by the focused tests.

## Final evidence

- Generator SHA-256: `2f8f6702032dd60e54f9c9e0859c71f76688610fbc89e10d4a1913541c283e4a`.
- Final battery: 12/12 green (`checks/after-final-3/checks/8862a204ce3a_after_battery_summary.json`).
- Focused tests: 17/17 (`checks/task-tests-final-2/result.json`).
- Semantic smoke: 12/12 ordered lessons and 48/48 rotations; strict 308/600; each witness 292/600.
- Census: 300 lessons (100/band), 1,200 pairs, 1,179 unique inputs, zero declared-rival ambiguity in production or 1,200 rotations (`checks/lesson-census-final.json`).

## Known limits and open findings

The generator samples ten explicit profiles rather than every grid dimension, enforces distinct header colors, and bounds each control class at three cells. These are distribution choices, not restrictions in the Racket law. The semantic result is finite and rival-relative: it strongly covers the two shortcuts exposed by the canonical set but does not prove uniqueness against undeclared programs. No open blocker remains for this repair; catalog approval/training admission is intentionally outside reviewer scope.
## Current reviewer considerations

Source SHA-256: `2f8f6702032dd60e54f9c9e0859c71f76688610fbc89e10d4a1913541c283e4a`.

# Decisions — 8862a204ce3a

All decisions below apply to generator version 3.0.0. The canonical Racket law was treated as fixed. “Probe” paths are relative to the packet root.

## D0 — Use the pinned baseline and canonical ledger as authority

**Prior state.** No integrated prior return or substantive associated-note entry was available. The packet-pinned v2.0.1 file was therefore the measured baseline; retained task `b90d4c3d5553` was consulted only for the shape of a modern semantic contract.

**Choice.** Pin `RULE_HASH="067caed98cc7"`, keep the canonical Racket source unchanged, and make every Python reference helper subordinate to that authority.

**Alternatives rejected.** Rewriting the rule to preserve decoys would have encoded a generator artifact rather than the canonical task. Leaving the rule unpinned would preserve source-divergence risk.

**Probe/evidence.** Canonical ownership and mirror equality are tested over all five labeled pairs. Final `rule_smoke`, `racket_lint`, and `authority_sync` are green in `checks/after-final-3/`.

**Failure mode/limit.** The Python mirror can still drift in a later edit; the rule pin and canonical-pair test are the guard, while actual labels remain Racket-produced.

## D1 — Replace hard-coded three-marker/fourth-color scenes with profile signatures

**Prior choice reversed.** v2.0.1 always used rows `1`, `h//2`, and `h-2`, three distinct marker colors, and two decoys in a fourth color.

**New choice.** Define ten unique `(height, width, marker-count)` profiles: all five canonical signatures plus five disjoint broad signatures. Draw two or three distinct nonzero header colors according to the selected profile.

**Reason.** The canonical set contains both two- and three-header tasks and only two or three nonzero colors. The prior fixed five-object/four-color grammar was detectably off-distribution and created an irrelevant palette shortcut.

**Alternatives rejected.** Independent random `h`, `w`, and marker-count axes could collide and make a named profile unobservable. Copying only the five canonical signatures would under-diversify. Unbounded dimensions would add unsupported extrapolation.

**Probe/evidence.** `test_rule_pin_and_all_canonical_pairs_are_owned`, exact override cross-products, final distribution gate, and `checks/after-final-3/checks/8862a204ce3a_after_profile_floor.json` (38/60 exact, 60/60 envelope).

**Failure mode/limit.** The generator does not cover every rectangular size; support is intentionally finite and explicit.

## D2 — Advertise only pixel-observable controls

**Choice.** Retain two public axes: `scene_profile` and `row_layout`. Give each a literal enum domain and implement `observe_overrides` so generated pixels recover both values exactly.

**Alternatives rejected.** Keeping palette-family, density, or texture labels would preserve singleton/dead controls and overlapping semantics. An internal `canonical/contrast` branch is not advertised because it is a curriculum schedule rather than an exact user override.

**Probe/evidence.** The focused test crosses 10 profiles × 4 row layouts × 4 difficulty values and checks exact observation. Final override/lint stages pass.

**Failure mode/limit.** `row_layout="both"` fixes both boundary rows and, for three markers, adds one interior row; it does not control that interior row's exact coordinate.

## D3 — Alternate clean anchors and contrast witnesses

**Choice.** Use a deterministic two-slot schedule `canonical, contrast` and `EXAMPLES_NEEDED=3`.

**Reason.** Clean anchors preserve source style and distribution fit. Contrast items are required because every canonical input is sparse enough that two wrong rules fit all five labeled examples. Alternation guarantees every consecutive three-demo window contains at least one contrast item.

**Alternatives rejected.** Pure random witness injection has a nonzero chance of producing an all-clean lesson. All-contrast lessons would weaken source resemblance. Raising the minimum demonstrations without scheduling the critical variation would spend tokens without guaranteeing identifiability.

**Probe/evidence.** Focused enumeration of 12 starts/band and all four held-out query positions; 12-lesson semantic smoke; 300-lesson census with rotations.

**Failure mode/limit.** The production census does not enumerate every possible seed forever; the period-two contract and focused cyclic test provide the stronger schedule guarantee for declared rivals.

## D4 — Put both rule-critical controls in every contrast scene

**Choice.** Each contrast scene contains 1–3 nonzero cells in zero-header rows and 1–3 cells in marked rows whose colors conflict with the header.

**Reason.** The first control distinguishes “clear zero-header rows” from preserving their contents. The second distinguishes “overwrite the entire marked row” from filling blanks only. Making both mandatory means one contrast demonstration refutes both rivals.

**Alternatives rejected.** Splitting witness types across separate random examples would require a longer or more complex schedule. A single fixed decoy coordinate could itself become a shortcut.

**Probe/evidence.** `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `checks/after-final-3/checks/8862a204ce3a_after_semantic_gate.json`, and retained `counterexamples/overwrite_and_clear.json`.

**Failure mode/limit.** Only these two canonical-fitting rivals are declared; other program hypotheses remain outside the finite contract.

## D5 — Reuse header colors for controls

**Choice.** Contrast noise uses only the sampled header-color set.

**Reason.** This isolates the row semantics. A new fourth color would let a learner identify “decoy” by palette role rather than by row/header relation and would recreate the baseline distribution mismatch.

**Alternatives rejected.** Dedicated decoy colors and fixed numeric colors were both stronger nuisance cues. Same-header repeats in a marked row were excluded because they do not test overwrite semantics.

**Probe/evidence.** `self_check` rejects undeclared colors and same-header repeats outside column zero. Generated witness tests and final defect-lint pass.

**Failure mode/limit.** Distinct marker colors are enforced, so the sampler does not test two headers sharing a color. The canonical set also uses distinct headers; this is a documented domain choice rather than a rule requirement.

## D6 — Make validation mutation-sensitive

**Choice.** Validate rectangular integer grids, known profile signatures, exact marker count, distinct header colors, palette closure, no same-header repeats, and bounded control counts. Define `strict_canonical_like` as an exact canonical signature with no off-header nonzero cells.

**Reason.** The prior check accepted structure-destroying mutations and could not support trustworthy distribution statistics.

**Alternatives rejected.** Acceptance-only type/range validation cannot detect profile drift. Requiring every generated input to be strict would reject necessary teaching counterexamples.

**Probe/evidence.** Targeted impostor tests; final self-check stage; strict rate 308/600 (51.33%) against a declared 45% floor; all five canonical inputs accepted.

**Failure mode/limit.** The validator describes the intended training domain, not the full mathematical domain of the canonical rule.

## D7 — Keep difficulty semantically neutral but observably live

**Choice.** Difficulty applies a profile-index offset within the same canonical or broad group. It changes generated bytes while preserving branch type, validation, and exact override availability.

**Reason.** The first repair left bands identical and was correctly flagged as dead. There is no justified notion that this simple rule is intrinsically harder at one profile than another, so the bands should vary coverage rather than alter the law.

**Alternatives rejected.** Adding more noise by band could entangle “difficulty” with a rule cue. Narrowing profiles per band would break exact override support.

**Probe/evidence.** Retained intermediate failure in `checks/after-final/checks/8862a204ce3a_after_defect_lint.log`; `test_difficulty_bands_are_live_and_keep_each_branch_valid`; final defect-lint PASS.

**Failure mode/limit.** The bands are diversity partitions, not calibrated human/model difficulty levels.

## D8 — Declare executable rivals instead of prose-only claims

**Choice.** Provide `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable`.

**Reason.** Correct per-grid labels do not establish that a three-example lesson teaches the intended rule. The two audit targets demonstrate that unscheduled rule-critical variables can leave a plausible shortcut alive.

**Alternatives rejected.** A prose summary cannot be scored. Generic identity/rotation rivals miss this task's actual ambiguity. Assuming canonical examples are sufficient is contradicted by the rival fit over all five pairs.

**Probe/evidence.** Both declared shortcuts fit 5/5 canonical pairs, are refuted in 100/100 lessons per band, and survive in 0/1,200 query rotations in `checks/lesson-census-final.json`.

**Failure mode/limit.** Passing a finite rival library is not universal identifiability; this is stated in generator notes and review limits.

## D9 — Preserve a minimal, portable counterexample and task-local test suite

**Choice.** Retain `counterexamples/overwrite_and_clear.json` and 17 focused tests using `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

**Reason.** Future agents need a small witness that explains why the contrast branch exists, plus portable checks that do not depend on the packet's source depth.

**Alternatives rejected.** Keeping only large battery logs would make the core regression hard to understand and slow to replay. Editing the frozen root fixture was prohibited and unnecessary.

**Probe/evidence.** The counterexample test was first observed red when the JSON was absent (`checks/counterexample-red.log`) and then green; `checks/task-tests-final-2/result.json` records 17/17 in the isolated runtime.

**Failure mode/limit.** The JSON is a semantic witness, not a full representative sample of the output distribution.
