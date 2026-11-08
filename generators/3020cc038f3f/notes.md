# Working notes: 3020cc038f3f

## Review outcome (2026-10-03)

The v3.0.1 baseline generated valid-looking examples but exposed an untruthful control surface: no `RULE_HASH`, dead texture aliases, singleton axes, broad unsampled dimension claims, negative fixtures in the ordinary texture domain, silent unknown overrides, and thousands of undeclared band/override conflicts. It also forced partial overlap even though an identical-operand canonical profile exists, and its validator only checked control/color presence.

The selected v4.0.0 rewrite:

- pins canonical rule hash `d73f3f4b1c32` without changing canonical Racket semantics;
- advertises only exact observable axes (`grid_h`, `grid_w`, `ctrl`, `overlap_kind`);
- enumerates connected 3–6-cell normalized masks and constructs separated placements;
- supports partial and identical relations independently of control;
- validates the full calibrated input grammar and exposes `observe_overrides`;
- retains a supplementary Python oracle plus a canonical-fitting shape-statistics rival;
- declares six semantic witnesses and shared rival mappings;
- includes 144 task-local tests and `workspace/reference_probe.py`.

A first constructive version crashed at seed 424 because it fixed a three-cell second size before verifying a partial partner existed for a six-cell first mask. The final implementation pools all feasible partners across allowed sizes. A dedicated regression and a 10,000-draw stress probe cover this failure.

Final generator SHA-256:
`d1146b11df322c90910f6012a09c44ae4a60cb68a63c23bbed79d2539a202653`.

Final evidence:

- exact 12-stage after battery: `checks/after/`;
- portable task tests, 144/144: `checks/task-tests/`;
- independent 160-per-band Racket-backed audit: `checks/probe/lesson_audit.json`;
- failed test-first baseline: `checks/red-task-tests/`;
- reports and decisions: packet-root `REVIEW.md` and `DECISIONS.md`.

Imported associated notes remain in `evidence/associated_notes.jsonl`; that file was empty in this packet.
## Current reviewer considerations

Source SHA-256: `d1146b11df322c90910f6012a09c44ae4a60cb68a63c23bbed79d2539a202653`.

# Decisions for 3020cc038f3f

Each decision records the selected input choice, the rationale available at review time, rejected alternatives, probes, failure modes, and limits. Finding IDs refer to `REVIEW.md`.

## D1 — Preserve the canonical Racket rule

**Choice.** Keep canonical rule hash `d73f3f4b1c32` and repair generation rather than redefine labels.

**Rationale.** All four canonical pairs execute correctly under the selected rule; the defects were in API truthfulness, manifold coverage, validation, and teaching support. Changing the rule would have introduced a new authority question without solving those data problems.

**Alternatives considered.** Simplify the rule to assume only partial overlaps; rejected because an identical-operand canonical profile exists. Replace the rule with the Python mirror; rejected because Racket is the declared label authority.

**Probe.** Final rule smoke, authority sync, canonical profile gate, and 41-grid real-Racket parity in `checks/probe/lesson_audit.json`.

**Limit.** Python parity is supplementary; an untested DSL edge could still differ outside the generator domain.

## D2 — Replace nine nominal axes with four observable exact controls (R1)

**Choice.** Advertise only `grid_h`, `grid_w`, `ctrl`, and `overlap_kind`.

**Original rationale.** Unknown. The baseline exposed `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, and `texture`, but several were singleton, ignored aliases, or ordinary-domain negative fixtures.

**Alternatives considered.** Keep aliases for compatibility; rejected because a declared override must alter or observably select lawful output. Mark singleton values diagnostic; rejected because they add no useful generator control. Keep degenerate textures; rejected because invalid controls and missing blobs are not training examples for the canonical task.

**Probe.** Exact override Cartesian product in the 144-test suite and the shared override gate: 5,310 accepted draws, 59 cases, three bands, zero explicit rejections; unknown keys fail loudly.

**Failure mode addressed.** Silent typos and apparently successful controls that do nothing.

**Limit.** This intentionally breaks callers that relied on undocumented ignored/negative keys; failing loudly is the desired contract.

## D3 — Use narrow canonical-supporting dimensions in every band (R1, R2)

**Choice.** `grid_h=7..9`, `grid_w=9..11`; default weights favor heights 7/8 and width 10 while all values remain legal in all bands.

**Rationale.** The baseline declared 5..14 / 7..14 but sampled only a subset and produced 21/60 exact profile hits. The repaired range reflects actual lawful usage and improves canonical support without copying canonical grids.

**Alternatives considered.** Honor the old full ranges; rejected because it would require a much broader distribution without canonical evidence. Make difficulty ranges disjoint; rejected because exact overrides would become band-incompatible.

**Probe.** Profile floor 45/60 in the final battery and exhaustive override tests.

**Limit.** The generator does not claim that larger canvases are semantically invalid; they are outside this calibrated training manifold.

## D4 — Enumerate connected 3–6-cell masks up to 4×4

**Choice.** Build a deterministic cached bank of all normalized 4-connected masks with 3–6 cells fitting a 4×4 bounding box.

**Rationale.** This retains the documented operand scale, greatly exceeds the old eight-shape bank, makes feasibility known before placement, and avoids arbitrary retry exhaustion.

**Alternatives considered.** Continue random growth with capped retries; rejected after the baseline's fallback risk. Use a small curated bank; rejected for lower geometry diversity. Enumerate larger masks; rejected as unnecessary for the canonical scale and current canvases.

**Probe.** Diversity gate, 10,000-draw stress run, and task-local uniqueness assertions.

**Failure mode addressed.** Low output codomain and retry paths returning a stale or malformed last grid.

**Limit.** Sampling is not uniform over free polyominoes; the bank is a bounded curriculum, not a combinatorial prior.

## D5 — Make relation independent of control (R2, R3)

**Choice.** Sample `overlap_kind` with a default 3:1 weighting of partial to identical, independently of `ctrl`.

**Rationale.** Canonical examples admit a shape-statistics shortcut that infers the operation without reading the control. Crossing control with relation breaks that correlation, while retaining the common partial-overlap case.

**Alternatives considered.** Partial only; rejected because it excludes canonical identical operands. Add disjoint masks; rejected because union and XOR become equivalent and there is no canonical support requiring that extra ambiguity. Balance 1:1; rejected as more drift than needed; exact overrides still allow balanced external schedules.

**Probe.** Final semantic gate: 343/600 shortcut-refuting examples; independent probe: 81–89 disagreements per 160 draws per band.

**Failure mode addressed.** Training a model to infer the set operation from operand statistics instead of `(0,0)`.

**Limit.** Identical operands themselves do not distinguish union from intersection; identifiability is lesson-level, not per-example.

## D6 — Construct separated physical placement directly (R5)

**Choice.** Choose a feasible horizontal or vertical composition, then place each operand with at least one blank separator row or column.

**Rationale.** Physical separation is part of the task grammar and prevents same-color/object parsing ambiguities. Direct construction is faster and eliminates nested bounded rejection loops.

**Alternatives considered.** Enumerate every placement pair; implemented briefly, then rejected as avoidably quadratic. Random independent placement plus rejection; rejected for unpredictable rare failures.

**Probe.** Blank-separator mutation tests, exact override stress, and rule smoke.

**Failure mode addressed.** Touching bounding boxes, overlap with the control, and performance degradation.

**Limit.** Placement orientation is not an advertised axis; it is nuisance variation.

## D7 — Select partial partners only after feasibility is known (R5)

**Choice.** Given the first mask, pool all partial-overlap partners across difficulty-allowed sizes and then draw from the feasible pool.

**Rationale.** The first rewrite selected a second size before checking feasibility. Seed 424 exposed a six-cell first mask for which no triomino met the strict partial relation.

**Alternatives considered.** Retry another first mask; rejected because it hides a deterministic unsupported branch. Add special cases by size; rejected in favor of direct feasibility.

**Probe.** Dedicated seed-424 regression plus 10,000 generated draws.

**Limit.** Uniformity is over feasible partner masks, not over size pairs.

## D8 — Enforce the full input grammar in `self_check` (R4)

**Choice.** Validate dimensions, rectangularity, integer cells, exact palette, unique control, one connected component per operand, 3–6 cells, blank bbox separator, and partial/identical normalized relation.

**Rationale.** A validator used as a strict profile must reject semantic impostors, not merely confirm color presence.

**Alternatives considered.** Keep validation permissive to accept larger lawful variants; rejected because the generator advertises a calibrated domain and the shared gates use validator acceptance as evidence. Validate outputs too; rejected as a separate concern handled by the rule/oracle tests.

**Probe.** 60/60 battery mutations rejected and targeted task-local mutations.

**Limit.** The validator recognizes this generator's manifold, not all conceivable inputs on which the Racket program can execute.

## D9 — Retain one explicit canonical-fitting rival (R3)

**Choice.** Declare `shape_statistics_shortcut` in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, mapped to `control_not_shape_statistics`.

**Rationale.** It exactly fits all four public pairs and is therefore a realistic learner shortcut. Executable rivals make claims falsifiable and let shared gates test generated counterexamples.

**Alternatives considered.** List many arbitrary wrong rules; rejected because breadth without canonical fit adds noise. Rely only on branch-frequency witnesses; rejected because frequency does not prove that a shortcut is refuted.

**Probe.** Shared semantic gate and `workspace/reference_probe.py`.

**Limit.** Other rivals may exist; this is the strongest reproduced one, not an exhaustive version space.

## D10 — Keep the Python oracle supplementary

**Choice.** Add `oracle_output` for transparent unit tests and a separately derived workspace oracle, but continue to execute Racket for authority checks.

**Rationale.** Fast local tests need a readable expected result, while source-bound Racket parity protects against copying the same Python mistake into both generator and tests.

**Alternatives considered.** Invoke Racket in every unit test; rejected as slow and brittle. Trust only the Python oracle; rejected as circular relative to the declared authority.

**Probe.** 41/41 real-Racket parity in the independent audit.

**Limit.** Only 41 probe grids were sent through Racket; the main rule-smoke gate supplies broader runtime coverage.

## D11 — Synchronize archival authority text without semantic change (R6)

**Choice.** Make archival `target_code` byte-equal to its existing `raw_code`.

**Rationale.** The texts differed only by comments, and sampled behavior already matched. Synchronization removes misleading source-drift warnings while preserving the executable program.

**Alternatives considered.** Leave the warning; rejected because it obscures meaningful authority drift. Replace canonical text; rejected because canonical authority did not need modification.

**Probe.** Final defect lint and authority-sync execution parity.

**Limit.** This is a representation cleanup, not evidence that all future edits will remain synchronized.

## D12 — Build source-bound reusable review tooling

**Choice.** Add `workspace/reference_probe.py` and 144 task-local regressions.

**Rationale.** Future reviewers need an independent oracle, canonical-shortcut check, per-band 100+ draw audit, unique-input/output counts, determinism check, and optional no-fallback Racket parity in one command.

**Alternatives considered.** Keep ad hoc notebook/terminal probes; rejected because they are not replayable. Put the probe in production generator code; rejected to keep review tooling separate.

**Probe.** `checks/probe/lesson_audit.json` records the tool hash, generator hash, sampler, counts, and Racket result.

**Limit.** The probe is task-specific by design; its matched-counterfactual idea should be promoted to a shared gate separately, as proposed in `QUESTION_ANSWER.md`.

## Current review outcome (2026-10-24, review-121bb3e4ee077281)

Production `generator.py` remains byte-identical at
`d1146b11df322c90910f6012a09c44ae4a60cb68a63c23bbed79d2539a202653`;
the canonical rule was not changed. A native task-local family now exposes
`preprocess=identity` (the exact canonical program) and
`preprocess=rotate_larger_cw`.

The alternate has a real input-dependent dependency: Step A normalizes both
operands and compares occupied-cell counts, producing `selected_color` for the
larger operand (ties choose color 1). Step B rotates only that selected operand
clockwise before the visible control chooses union, XOR, or intersection. The
standardized protected-Racket witness uses a qualified seed-17 query; replacing
`selected_color=2` with the smaller color 1 changes six padded output cells.

The family supports 2–6 prefix-stable demonstrations and 1–4 prefix-stable,
distinct queries. Inputs are identical across settings. The first two demos swap
which color is larger, so fixed-color, skipped-selection, wrong-rotation,
bbox-area, and fixed-operation rivals are constructively refuted. Query four is
a substantive 30×30 case rather than padded small content.

Retained evidence:

- 13 focused parametric tests plus the full task suite, 157/157 passed;
- 240 structural episodes, 1,920 visible pairs, every demo count 2–6, 240
  substantive 30×30 checks, and zero finite-rival failures;
- 12 protected-Racket audit jobs, demo counts 2/3/6, 39 unique evaluations;
- native qualification of both settings on seeds 0 and 17, 4/4 jobs and 40
  protected-Racket evaluations;
- public first-turn export check over eight saved challenges, with no hidden
  settings, programs, future queries, or labels exposed;
- standardized source-bound causal witness and reviewer replay under
  `checks/3020cc038f3f/causal/`.

Limits: the rival set is finite and does not prove universal identifiability or
training value. Reviewer status is ready only. The owner must integrate these
exact bytes, rerun native qualification, replay the witness, and perform fresh
acceptance; `training_admitted` remains false.
