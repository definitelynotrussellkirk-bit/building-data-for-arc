# Current notes: 5b4fd0a9c80e

## Intended rule

Find every same-color 4-connected nonzero component. Crop each component's raw
bounding box, sort crops by `(cell count, bbox top row, bbox left column)`, and
stack them vertically with one all-zero row between crops. The output width is
the widest crop; each crop is horizontally placed at
`floor((output_width - crop_width) / 2)`. The selected Racket authority is
unchanged and pinned by `RULE_HASH = d54b19002e00`.

## Baseline findings

The issued v2.1.0 sampler used only distinct areas, so it never taught the
canonical positional tie break. It also omitted the rule hash and semantic
contract, advertised controls it did not honor, accepted unknown controls, had
dead axes, produced identical difficulty bands, and allowed a left-alignment
shortcut. No prior return was treated as evidence; these findings were measured
against the packet's pinned baseline under `checks/before/`.

The strongest canonical shortcut is **left-align every crop**. It matches all
five labeled canonical pairs because their widest crop has width 3 and every
narrower crop has width 2, for which floor-centering also gives offset 0. The
source-bound counterexample in `counterexamples/left-align-vs-center/` is emitted
by seed 42 / sample 0 and has a width-2 crop inside a width-4 output, where the
intended offset is 1.

## Selected design (v4.0.0)

The sampler is constructive and rejection-free. A four-profile cyclic schedule
alternates two three-distinct-area lessons with two equal-area lessons:

- profile 0: areas `(3,5,7)`, source order `(5,7,3)`, and a cell-area versus
  bbox-area conflict;
- profile 1: areas `(4,4,6)`, with the earlier tied crop higher but farther right,
  proving that top row precedes left column;
- profile 2: areas `(4,6,7)`, source order `(6,4,7)`, defeating both source order
  and “move the largest object last”;
- profile 3: areas `(5,5,7)`, with tied crops sharing a top row, making left column
  observable as the secondary key.

Every profile contains odd crop-width differences and a required blank separator.
Every three-demo cyclic window contains a distinct-area trap and a positional tie.
Difficulty shifts the same four-profile cycle (`easy +0`, `medium +1`, `hard +2`)
so bands are not byte-identical while retaining equal semantic coverage.

Exact controls are `grid_h=10..14`, `grid_w=12..16`, and `shape_profile=0..3`.
They are validated before drawing, honored without clipping/fallback, and recovered
from pixels by `observe_overrides`.

## Executable semantic contract

`rule_mirror` mirrors the selected authority. Declared rivals are left alignment,
right-biased centering, color tie-breaking, color-only ordering, source ordering,
move-largest-last, bbox-area sorting, and omitted separator rows. Witnesses and
`WITNESS_RIVALS` are executable, and `lesson_identifiable` rejects malformed or
mislabelled pairs and any lesson on which a declared rival survives all demos.
`workspace/reference_probe.py` independently checks the mirror, canonical fit,
and complete lessons.

## Limits

The sampled domain deliberately remains three components, areas 3..7, grids
10..14 by 12..16, and distinct component colors. The finite rival set and sampled
lesson census do not prove unique logical induction against every possible rule.
Difficulty changes schedule phase rather than defining easier/harder geometry.
The Racket authority and canonical ledger were not changed.
## Current reviewer considerations

Source SHA-256: `35e8bdcacaed9f450dbfa0e7ec2c9c7ea091fde58d77a2693a53e6f6490941f4`.

# Decisions for 5b4fd0a9c80e

## D1 — Preserve the selected Racket authority

**Decision.** Keep the canonical rule and ledger unchanged, pin the generator to `RULE_HASH = d54b19002e00`, and repair only the selected generator, tests, notes, probe, and counterexample.

**Rationale and evidence.** The canonical executable rule consistently extracts same-color 4-connected components, sorts by `(cell count, bbox top, bbox left)`, and stacks raw bbox crops with one blank row and floor-centered horizontal placement. The baseline rule smoke and authority checks were already green; the failure was the sampler/teaching contract, not rule execution. Final authority evidence is under `checks/after/checks/5b4fd0a9c80e_after_rule_smoke.json` and `checks/after/checks/5b4fd0a9c80e_after_authority_sync.json`.

**Rejected alternative.** Changing the rule to fit the baseline's distinct-size-only behavior would erase canonical tie semantics and turn a generator defect into an authority change.

**Limit/future check.** Re-run authority sync and the independent probe whenever the selected rule text or canonical row changes.

## D2 — Use a constructive four-profile schedule

**Decision.** Replace unconstrained random shape sampling and rejection with four explicit semantic profiles, selected cyclically.

**Rationale and evidence.** A finite constructive schedule makes every teaching contrast inspectable: profiles 0 and 2 prove real area sorting; profiles 1 and 3 prove top-row and left-column tie keys. It also guarantees odd centering offsets and blank separators without retry bias. `checks/lesson-census.json` found 0 ambiguous production lessons in 300 and 0 ambiguous rotations in 1,200.

**Rejected alternatives.** Randomly sampling three arbitrary components would require rejection to obtain ties and would make witness frequency probabilistic. Keeping only distinct areas was rejected because it cannot identify the positional tie break.

**Reversal preserved.** The first four-profile draft placed one large object before an equal pair in every lesson. An executable “move largest last” rival survived, so that draft was replaced by two true three-size sort profiles; the final generator retains this rival as a regression check.

**Limit/future check.** Any profile edit must rerun every cyclic three-demo window and all query rotations, not only individual-pair label checks.

## D3 — Three demonstrations, cyclic order, next-pair query

**Decision.** Declare `EXAMPLES_NEEDED = 3`; assemble consecutive profiles from the four-profile cycle and use the next accepted pair as the normal query. Support every hold-one-out query rotation as well.

**Rationale and evidence.** Three demonstrations are the smallest window that can always contain one distinct-area trap plus one positional-tie witness under this four-profile schedule. The strict semantic gate passed all 48 diagnostic rotations, and the larger required census passed all 1,200 rotations (`checks/semantic-rotations/`, `checks/lesson-census.json`).

**Rejected alternative.** A two-demo lesson can omit either true multi-size sorting or one positional tie key, depending on its cyclic start.

**Limit/future check.** This claim is bound to the current schedule and declared rivals; it is not a proof against undeclared hypotheses.

## D4 — Expose only exact observable controls

**Decision.** Keep three axes: `grid_h=10..14`, `grid_w=12..16`, and `shape_profile=0..3`. Validate all requests before drawing, reject unknown keys, and expose `observe_overrides`.

**Rationale and evidence.** The baseline advertised controls it did not honor and accepted typoed keys. The final override gate executed all 82 cases across three bands and 30 seeds—7,380 draws—with zero findings and rejected the unknown-key probe (`checks/after/checks/5b4fd0a9c80e_after_override.log`).

**Rejected alternatives.** Singleton “palette size” or “number of colors” axes were removed because they are not meaningful controls. Silent clipping/fallback was rejected because it makes requests appear successful without changing pixels.

**Limit/future check.** New axes require an exact pixel observer and full joint-override matrix coverage.

## D5 — Keep a narrow, explicit sampled domain

**Decision.** Generate exactly three nonzero components, each a distinct color, with areas 3–7 and bboxes at most 5×5 on 10–14 by 12–16 grids.

**Rationale and evidence.** This envelope is broad enough to expose every selected semantic contrast while keeping construction deterministic and reviewable. The profile floor passed 60/60 exact-profile and 60/60 envelope samples, and the independent probe saw 1,599 unique generated inputs out of 1,600 pairs.

**Rejected alternative.** Expanding to repeated colors, more components, or arbitrary areas was not needed to repair the documented teaching defects and would introduce new connectivity/order interactions.

**Limit/future check.** The validator owns canonical inputs beyond the production sampler where compatible, but the sampled curriculum does not claim coverage of all authority-valid grids.

## D6 — Make rivals executable and source-bound

**Decision.** Declare executable rivals for left alignment, right-biased centering, color tie-breaking, color ordering, source order, move-largest-last, bbox-area sorting, and omitted separator rows. Map each witness to the rivals it refutes and reject lessons where any declared rival survives.

**Rationale and evidence.** Boolean metadata alone cannot establish a counterexample. The shared semantic gate verified 8/8 witness claims, and `workspace/reference_probe.py` independently scored the live rival declarations. `checks/reference-probe-final.json` found zero survivors over 400 complete lessons.

**Rejected alternative.** Hard-coded rival-name lists in the probe were rejected; the probe imports and scores the generator's live declarations so additions cannot silently escape coverage.

**Limit/future check.** Rival completeness remains finite; add newly discovered shortcuts both as executable competitors and focused tests.

## D7 — Treat difficulty as schedule phase, not claimed hardness

**Decision.** Offset the profile cycle by 0/1/2 for easy/medium/hard.

**Rationale and evidence.** The baseline emitted byte-identical bands. Phase shifting makes bands materially different while preserving equal rule coverage and avoiding unsupported claims that one geometry is cognitively harder. `test_difficulty_bands_select_distinct_declared_schedule_profiles` and the final distribution/semantic gates cover this behavior.

**Rejected alternative.** Artificially enlarging grids or adding clutter by band was not justified by canonical evidence and could create confounded shortcuts.

**Limit/future check.** Do not interpret band names as calibrated difficulty until a separate solve-performance study exists.

## D8 — Retain an exact canonical-shortcut counterexample

**Decision.** Store seed 42/sample 0 under `counterexamples/left-align-vs-center/` with input, supported Racket output, Python mirror, rival output, source hashes, and replay metadata.

**Rationale and evidence.** Left alignment matches all 5 canonical labeled pairs, so a concrete emitted disagreement is essential. The retained input has a width-2 crop inside a width-4 output: the authority begins it at column 1, while the rival begins at column 0. `tests/test_generator.py::test_retained_left_alignment_counterexample_replays_exactly` prevents drift.

**Rejected alternative.** A prose-only statement was rejected because it cannot be replayed or source-bound.

**Limit/future check.** Regenerate the Racket receipt and update the binding if either generator or rule hash changes.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-54c3cb91af6294c0:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `35e8bdcacaed9f450dbfa0e7ec2c9c7ea091fde58d77a2693a53e6f6490941f4`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/5b4fd0a9c80e/generator.py,unchanged SHA256 35e8bdcacaed9f450dbfa0e7ec2c9c7ea091fde58d77a2693a53e6f6490941f4. No actionable issue within bounded checking.35 portable tests passed; initial combined audit failed only declared_period_not_enumerated, while12 lessons/48 diagnostic rotations and witness claims passed. Separate required semantic rerun with period4 enumeration passed on the same source. Finite fixed-seed schedule and declared rivals only; no universal uniqueness, target edit or new approval. No owner audit rerun. Target-local receipts: `checks/audit/5b4fd0a9c80e-combined-command.log` `checks/audit/5b4fd0a9c80e-combined/checks/5b4fd0a9c80e_audit_battery_summary.json` `checks/audit/5b4fd0a9c80e-combined/checks/5b4fd0a9c80e_audit_commands.jsonl` `checks/audit/5b4fd0a9c80e-combined/checks/5b4fd0a9c80e_audit_semantic_gate.json` `checks/audit/5b4fd0a9c80e-combined/checks/5b4fd0a9c80e_audit_semantic_gate.log` `checks/audit/5b4fd0a9c80e-combined/checks/5b4fd0a9c80e_audit_semantic_gate.receipt` `checks/audit/5b4fd0a9c80e-combined/checks/5b4fd0a9c80e_audit_summary.json` `checks/audit/5b4fd0a9c80e-combined/checks/task_tests.xml` `checks/audit/5b4fd0a9c80e-combined/progress.log` `checks/audit/5b4fd0a9c80e-combined/result.json` `checks/audit/5b4fd0a9c80e-semantic-final-command.log` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_battery_summary.json` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_commands.jsonl` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_semantic_gate.json` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_semantic_gate.log` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_semantic_gate.ok` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_semantic_gate.receipt` `checks/audit/5b4fd0a9c80e-semantic-final/checks/5b4fd0a9c80e_audit_semantic_gate.schedule-census.json` `checks/audit/5b4fd0a9c80e-semantic-final/progress.log` `checks/audit/5b4fd0a9c80e-semantic-final/result.json`

### Assessment or prior finding

## 5b4fd0a9c80e

**No issue found after checking.** Assigned/current generator SHA-256: `35e8bdcacaed9f450dbfa0e7ec2c9c7ea091fde58d77a2693a53e6f6490941f4`.

I inspected the constructive four-profile schedule, exact controls, executable rivals/witnesses, retained left-alignment counterexample, notes, and task-local tests. The portable task-test portion executed **35/35 passing**. The initial combined audit command exited 1 solely because strict semantic policy warned that the declared period 4 had not been natively enumerated; it still reported 12/12 identifiable lessons, 0/48 ambiguous diagnostic rotations, 8/8 firing witnesses, and 8/8 verified rival claims.

I then reran the semantic stage in a new output with `--enumerate-schedule-period --require-rotations-identifiable`; it passed. This checks every fixed-seed start in the declared four-step period and all query rotations against the finite declared rival set. I found no concrete counterexample or new plausible shortcut beyond the already-retained/refuted left-alignment rival.

Evidence:

- initial task tests and diagnostic semantic result: `checks/audit/5b4fd0a9c80e-combined/`;
- final required semantic result: `checks/audit/5b4fd0a9c80e-semantic-final/`.

Limit: the result is finite and source-bound; it does not prove uniqueness against undeclared hypotheses. No audit-target source was edited or approved.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
