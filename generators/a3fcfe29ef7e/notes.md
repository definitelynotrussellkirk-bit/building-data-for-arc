# Working notes: a3fcfe29ef7e

## Current intent

The input is an `h x 7` grid: two aligned three-column panels separated by one
solid column.  The output is `h x 3`; an output cell is color 3 exactly when the
aligned left and right cells are both zero.  The other Boolean occupancy states
`10`, `01`, and `11` output zero.  Canonical rule hash: `f7f19079511e`.

## Decisions in v3.0.0

- Replaced independent-density panel sampling plus post-hoc minimum enforcement
  with direct sampling of the four aligned occupancy states.  Every ordinary
  draw now contains `00`, `10`, `01`, and `11`; `both_zero_count` is exact.
- Reversed the old single-panel-color choice.  A two-step schedule alternates
  different and equal left/right foreground colors.  Canonical pairs use
  different colors, where the shortcut “mark raw-equal values” imitates NOR;
  an equal-color `11` cell is the decisive counterexample.
- Set `EXAMPLES_NEEDED = 4` and made every five-pair schedule window identifiable
  against the declared rivals under every held-out query rotation.
- Made all advertised controls exactly observable: height, three color roles,
  positive count, and layout.  The first three row-major non-`00` states encode
  one of six layout signatures so geometrically coincident samples cannot make
  the control unobservable.
- Kept negative fixtures (`no_both_zero`, `all_both_zero`, `same_panels`) outside
  `AXES`; they exercise the rule but are intentionally rejected by `self_check`.
- Added all-band canonical-profile anchors every fourth sample (height 4 and
  three distinct nonzero input roles).  This is coverage, not a claim that the
  generated distribution reproduces every canonical marginal.
- Synchronized the selected executable Racket target to the canonical program
  while preserving the archival `raw_code` verbatim.

## Reproducible evidence

- `tests/test_generator_a3fcfe29ef7e.py` covers canonical parity, exact controls,
  deterministic replay, negative fixtures, semantic rivals, lesson rotations,
  the schedule probe, and the retained counterexample.
- `counterexamples/raw-value-equality.json` is a generated equal-color `11`
  witness checked by the canonical Racket authority and the independent Python
  mirror.
- `workspace/probe_schedule_contract.py` enumerates every declared schedule
  start in all three bands and every permitted query rotation.

## Assumptions and limits

The separator is one constant nonzero color, color 3 remains output-only, each
panel uses background plus one foreground, height is 3..18, and ordinary draws
contain 1..6 `00` cells.  Identifiability evidence is finite and only covers the
named executable rivals; it is not a proof against every possible program.  The
layout signature is intentionally observable but somewhat synthetic.  No model
training or Qwen inference experiment was run, so downstream learning value is
unknown beyond the structural and rival-based gates.
## Current reviewer considerations

Source SHA-256: `60abc70da2e95445a5c82f531700245d9da03050f658e721718e4365949c23db`.

# Decisions for a3fcfe29ef7e

## D1 — Preserve the canonical rule; synchronize only the selected executable target

**Choice.** Keep canonical rule hash `f7f19079511e` unchanged.  Replace the selected
base record's `target_code` with the exact canonical program while preserving its
historical `raw_code` and recording `canonicalization_status`.

**Rationale.** The baseline rule smoke showed the reference behavior was sound, and
all six canonical pairs express the same cellwise NOR law.  The defect was source
selection and generator support, not the law.  Synchronizing the selected target
removes ambiguity for execution and review without erasing provenance.

**Rejected alternatives.** (1) Rewrite the canonical Racket rule: unnecessary and
higher risk.  (2) Delete or overwrite `raw_code`: loses useful archival evidence.
(3) Merely suppress the divergence warning: leaves the selected authority unclear.

**Probe/evidence.** Final authority-sync and rule-smoke stages under
`checks/after-final-v2/checks/`; canonical counterexample apply receipt under
`checks/counterexample/`.

**Failure modes and limits.** The archived source remains textually divergent by
design.  It is behaviorally equivalent on the six canonical pairs, not proven
equivalent over every possible grid.

## D2 — Sample aligned Boolean states directly

**Choice.** Construct every ordinary scene from explicit `00`, `10`, `01`, and
`11` assignments instead of drawing the panels independently and repairing the
positive branch afterward.

**Rationale.** The output depends only on the aligned occupancy pair.  Direct state
sampling makes the semantic support auditable, guarantees all four truth-table
rows, and makes `both_zero_count` exact rather than a lower bound.

**Rejected alternatives.** (1) Keep Bernoulli densities and retry until all states
appear: stochastic, wasteful, and hard to make exact.  (2) Patch only missing `00`
cells: still permits omission of negative states and hides control interactions.
(3) Restrict to canonical examples: too little diversity.

**Probe/evidence.** Focused tests inspect all four state counts; the semantic gate
ran 600 strict draws; override results exercised the complete advertised matrix.

**Failure modes and limits.** Requiring all four states means ordinary heights and
positive counts must leave at least three negative cells.  Incompatible requests
are rejected with structured axis names rather than silently modified.

## D3 — Make every advertised control exactly observable

**Choice.** Advertise `grid_h`, `left_color`, `right_color`, `sep_color`,
`both_zero_count`, and `layout`.  Encode each of six layouts using the first three
row-major non-`00` states, after reserving the exact positive cells.

**Rationale.** The review contract tests observed output, not merely accepted
arguments.  A geometric layout can coincide by chance on small grids, so a short
state signature makes the chosen value recoverable while preserving substantial
randomness in the remaining cells.

**Rejected alternatives.** (1) Leave the old unbounded `both_zero_target`: the
linter could not probe it and generation did not honor it exactly.  (2) Advertise
negative fixtures as textures: they are intentionally outside the ordinary law
support.  (3) Infer layout only from global geometry: ambiguous for some sizes.

**Probe/evidence.** `observe_overrides`, 40 focused tests, and
`checks/after-final-v2/checks/a3fcfe29ef7e_after_override_results.json`.

**Failure modes and limits.** The signature is synthetic and could itself become a
spurious feature, although it does not correlate with the output beyond the true
cell states.  Layout controls describe the ordering of states, not an exhaustive
geometric family.

## D4 — Alternate different-color and same-color panel profiles

**Choice.** Use a period-two schedule: `different`, then `same`, repeated in all
bands.  Preserve color 3 as output-only and require a distinct nonzero separator.

**Rationale.** On different-color panels, the wrong rule “mark raw-equal values”
agrees with NOR: only `0 == 0` is true.  A same-color `11` cell makes that rival
write 3 where NOR writes 0.  Alternation keeps canonical-like examples while
ensuring every four-demo-plus-query window contains a decisive witness.

**Rejected alternatives.** (1) Always one shared foreground color: rejects all
canonical inputs and omits canonical palette support.  (2) Always different colors:
leaves raw equality indistinguishable.  (3) Randomize profile independently: can
produce an ambiguous lesson by chance.

**Probe/evidence.** Retained counterexample, Racket receipt, schedule probe, and
rotation census.

**Failure modes and limits.** A two-step deterministic palette schedule is itself
visible.  The lesson contract checks eight named rivals, not every palette-based
heuristic a model might invent.

## D5 — Use four demonstrations and check every allowed query position

**Choice.** Set `EXAMPLES_NEEDED = 4`.  A lesson is four ordered demonstrations
plus one query; downstream query rotation is supported, so all five held-out
positions must remain identifiable.  Declare `LESSON_SCHEDULE_PERIOD = 2` and
verify both starts in each band.

**Rationale.** Four demonstrations provide room for both palette profiles while
showing all four Boolean states repeatedly.  Rotation checks prevent the only
counterexample from being moved into the query and disappearing from the demos.

**Rejected alternatives.** (1) Three demonstrations: narrower witness redundancy.
(2) Check only the production final query: unsafe when training assembly rotates
pairs.  (3) Use a stochastic sample alone: may miss one schedule residue.

**Probe/evidence.** `workspace/probe_schedule_contract.py` checks 30/30 declared
schedule rotations; `checks/lesson-census-final.json` checks 1,500/1,500 production
rotations.

**Failure modes and limits.** Fixed-seed period enumeration does not exhaust random
support.  The 300-lesson stochastic census broadens support but remains finite.

## D6 — Add canonical-profile anchors without copying the canonical marginal

**Choice.** Every fourth sample uses canonical height 4 and three distinct input
roles; other draws span heights 3–18, legal colors, counts 1–6, and six layouts.

**Rationale.** The profile-floor gate requires support in every difficulty band,
but training should not collapse to six memorized grids.  Anchors provide regular
canonical geometry/palette contact while the remaining samples diversify state
placement and dimensions.

**Rejected alternatives.** (1) Difficulty-specific heights excluding 4 in hard:
fails profile support.  (2) Always canonical size: under-diverse.  (3) Claim the
anchor reproduces the canonical distribution: unsupported.

**Probe/evidence.** Profile floor found exact support in every band; diversity and
strict semantic reports are retained in the final battery.

**Failure modes and limits.** The 1-in-4 cadence is a pragmatic coverage choice,
not learned from downstream performance.

## D7 — Keep negative fixtures outside the ordinary axis contract

**Choice.** Retain `no_both_zero`, `all_both_zero`, and `same_panels` as explicit
negative/diagnostic fixtures, not valid `AXES` values.  `self_check` rejects them
for training admission.

**Rationale.** They are useful for testing rule branches and validator sensitivity,
but mixing them into the advertised production domain caused the baseline
texture-domain-overlap defect and weakened the truth-table guarantee.

**Rejected alternatives.** (1) Delete them: loses useful mutation tests.  (2) Mark
all lawful: contradicts the intended ordinary distribution.  (3) Silently resample:
hides caller mistakes.

**Probe/evidence.** Focused fixture tests and final defect-lint/self-check stages.

**Failure modes and limits.** `same_panels` can be mathematically lawful for NOR;
it is rejected here because it violates the chosen four-state teaching grammar,
not because the Racket rule cannot evaluate it.

## D8 — Retain reusable, source-bound diagnostics

**Choice.** Add a schedule enumeration tool, minimal counterexample, focused tests,
TDD red/green receipts, source-bound official reports, two audit reproducers, and a
clean-packet replay of the exact packager-generated patch.

**Rationale.** Future reviewers need to reproduce the exact defect and verify that
reported evidence used the final source bytes.  Small model-free probes are cheaper
and more diagnostic than a training experiment for structural curriculum faults.

**Rejected alternatives.** (1) Narrative-only review: not independently checkable.
(2) Keep only final green logs: conceals the original defect and test-first cycle.
(3) Run Qwen training as the primary test: costly and confounded for a finite rule
contract.

**Probe/evidence.** Paths are indexed in `REVIEW.md` and `RESULTS.json`.

**Failure modes and limits.** Test suites and declared rivals are necessarily
incomplete.  No empirical claim about model accuracy or data value is made.


## D9 — Treat packaging hygiene as part of correctness

**Choice.** Normalize the new probe helper to mode `0644`, remove generated
`repo/checks/` debris, and replay the exact patch bytes emitted by the return
packager before building the final archive.

**Rationale.** The packager correctly rejects executable changed source and
undeclared repository files.  Both failures were workspace metadata problems, not
semantic defects, but accepting them would make the return non-portable or
non-reproducible.

**Rejected alternatives.** (1) Bypass the packager checks: unsafe. (2) Delete the
probe: loses a reusable diagnostic. (3) Rely only on the earlier Git-generated
patch: it did not prove the exact return patch.

**Probe/evidence.** `checks/package-provisional.log` retains the first mode failure;
`checks/package-provisional-success.log` records successful validation;
`checks/package-patch-replay/receipt.json` records the exact-patch clean replay.

**Failure modes and limits.** Replaying the source patch does not independently
recompute every large battery artifact; it verifies application, source hashes,
focused behavior, and the schedule contract.

## D10 — Add a source-bound native parametric family without changing the canonical generator

**Choice.** Keep `row_policy="all"` as the exact byte-for-byte canonical program and
add one lawful alternative, `row_policy="densest"`, behind the native adapter in
`workspace/parametric/`.  The alternative first constructs the complete aligned-NOR
mask and per-row positive counts, then retains every row tied for the maximum count.
Demo and query counts are independent (`2..6` and `1..4`), while paired settings see
identical input grids.

**Rationale.** This creates a finite two-setting family with a real global dependency
rather than a cosmetic parameter.  The retained intermediate is the full mask plus
its input-dependent row-count vector and maximum; the protected-Racket intervention
replaces that vector with all zeros and changes both retained outputs.  Width remains
seven because the two three-column panels and separator are structural; stress is
therefore a lawful `30 x 7` input rather than an artificial square.

**Adversarial correction.** The first sampler always included a count-three row, so
"densest" accidentally collapsed to the local shortcut "keep rows with exactly
three positives."  A failing regression test exposed this.  The repaired schedule
mixes unique/tied maxima of two and three; the minimum three-demo lesson now refutes
exact-three, threshold-two, and single-winner tie rules.  A finite named-rival audit
found no demo-fit/query-disagree hole across 54 checks, but this is not a universal
program-uniqueness proof.

**Evidence.** Native inventory:
`workspace/parametric/evidence/manifest.json`; qualification and execution receipts:
`WORK/checks/a3fcfe29ef7e/qualification/`; causal witness and protected replay:
`WORK/checks/a3fcfe29ef7e/sequential-dependency-witness.json` and
`sequential-dependency-replay.json`.  The reusable
`WORK/checks/a3fcfe29ef7e/build_sequential_witness.py` rebuilds the witness after
future source-bound qualification changes.  Qualification is reviewer-reported;
owner acceptance and any training admission remain pending.
