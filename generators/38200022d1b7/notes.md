# Working notes: 38200022d1b7

## Baseline finding

The imported 1.1.2 sampler always placed the color-5 pivot at the geometric grid center and emitted only two singleton source cells in the upper-left. That distribution admitted at least two canonical-fitting shortcuts: rotate around the grid center, and copy only cells above the pivot. It also lacked `RULE_HASH`, exposed fake singleton axes, accepted unknown overrides, and declared no executable semantic contract.

Baseline generator SHA-256: `cedc7373c74caeb2e672d6dec4d097801e88c1b2fda667a714d75e2550b9851f`. The before battery recorded 8 green, 1 advisory, and 3 failed stages (`lint`, `defect_lint`, `override`) under `checks/before/`.

## Repair

Version 2.0.0 uses a four-position curriculum:

1. `canonical_two_blobs` — exact 9x9, 10x10, and 11x11 canonical dimension/palette/source-count anchors;
2. `quadrant_blob` — a one-component off-center-pivot case;
3. `axis_mix` — sources on both pivot axes;
4. `multi_quadrant` — sources on multiple sides of the pivot.

Seven exact observable controls replace the fake axes: grid height/width, pivot row/column offsets, source-cell count, source-color count, and layout profile. Construction is direct rather than rejection-based, and every joint boundary combination is legal.

The semantic contract names six rivals (`grid_center`, `above_only`, `move_instead_of_copy`, horizontal-only, vertical-only, and largest-component-only), maps witnesses to them, and requires four demonstrations. `workspace/counterexample_probe.py` emits a source-bound exact disagreement for the strongest canonical shortcut.

## Measured final state

Final generator SHA-256: `972a9fe6682f87810649cde398fa1c7e2692cfe58740badabb708becc2ab65d1`.

- Official after battery: 12/12 green (`checks/after/checks/38200022d1b7_after_battery_summary.json`).
- Portable task tests: 25/25 passed (`checks/task-tests-final/result.json`).
- Canonical profile floor: 3/3 canonical inputs accepted; 26/60 exact-profile hits, with nonzero support in every band.
- Semantic census: 138/600 strict canonical-like draws (23.0%, declared floor 20%); 12/12 smoke lessons identifiable.
- Required-rotation semantic stage: 60/60 query rotations identifiable.
- Source-bound lesson census: 300/300 lessons materialized, 0 ambiguous; 1,500/1,500 rotations checked, 0 ambiguous; 1,143 exact unique inputs.
- Post-repair visible solve: 4/4 demonstrations passed on revision 1, with earlier exposure declared `yes` and reference consultation `no`.

## Known limits

The sampler deliberately uses a finite template vocabulary, grids 9..13, pivots within one cell of grid center, 4..8 source cells, and 2..3 source colors. The finite rival census establishes separation only from the declared plausible rules; it is not a proof of universal identifiability. The selected Racket authority and canonical rows were not changed.
## Current reviewer considerations

Source SHA-256: `972a9fe6682f87810649cde398fa1c7e2692cfe58740badabb708becc2ab65d1`.

# Decisions for 38200022d1b7

## D1 — Keep the selected Racket authority unchanged and pin it

**Choice.** Add literal `RULE_HASH = "514de6262239"` and implement the Python generator/contract around the existing selected rule.

**Original rationale.** Unknown; the imported generator omitted the pin.

**Alternatives rejected.** Editing the Racket source or canonical rows to match the narrow baseline; dynamically deriving the hash. The canonical examples and execution authority already agree, and a literal pin is auditable.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` are green; the authority-set hash is unchanged.

**Failure mode/limit.** The Python mirror is supplemental evidence, never the output authority.

## D2 — Use a four-profile ordered curriculum

**Choice.** Repeat `canonical_two_blobs`, `quadrant_blob`, `axis_mix`, and `multi_quadrant`; require four demonstrations.

**Original rationale.** The baseline appears to have favored a minimal canonical-looking upper-left scene, but no retained note explains why.

**Alternatives rejected.** Pure random placement, which can omit a needed witness from a lesson; canonical-only placement, which preserves center/above shortcuts; raising demonstration count without a deterministic witness schedule.

**Probe.** Every five-pair query rotation is tested locally; the required-rotation semantic stage checked 60 rotations, and the larger census checked 1,500/1,500 with zero ambiguity.

**Failure mode/limit.** This is intentionally ordered and periodic. Although rotations pass for the declared competitors, finite schedules do not prove separation from every possible hypothesis.

## D3 — Replace broad/fake metadata with exact observable axes

**Choice.** Expose only seven controls recoverable from pixels and construct every declared joint combination directly.

**Original rationale.** The imported metadata likely followed an older generic schema (`position_bias`, `density`) rather than actual generator behavior.

**Alternatives rejected.** Keeping ignored compatibility axes; silently clamping impossible values; declaring a large incompatibility table.

**Probe.** `observe_overrides` round-trips requested values. The final override matrix used 30 seeds across 338 cases (30,420 draws) with zero findings, warnings, or explicit rejections.

**Failure mode/limit.** Exact controls describe the chosen 9..13 / center-neighborhood domain, not arbitrary grids or pivots.

## D4 — Preserve canonical morphology while adding counterfactual evidence

**Choice.** Put exact 9x9, 10x10, and 11x11 canonical dimension/palette/source-count anchors into the schedule, while using noncanonical profiles to expose causal distinctions.

**Alternatives rejected.** Maximizing diversity without anchors; copying canonical grids verbatim; requiring every draw to be strict-canonical-like.

**Probe.** All 3 canonical inputs pass `self_check`; profile floor reports 26/60 exact hits and support in every band; strict semantic support is 138/600 (23.0%) against the declared 20% floor.

**Failure mode/limit.** The exact strict rate varies under the pinned census and is not a guarantee for arbitrary seeds.

## D5 — Declare and execute plausible rivals

**Choice.** Encode six competitors and five witness classes, with `grid_center` and `above_only` explicitly marked as canonical shortcuts.

**Alternatives rejected.** Prose-only shortcut claims; relying only on output correctness; claiming universal identifiability from a finite list.

**Probe.** Every canonical shortcut fits all usable canonical pairs and has generated disagreements. `workspace/counterexample_probe.py` plus official `arcpuzzles apply` supplies an exact source/rule-bound grid-center counterexample.

**Failure mode/limit.** Undeclared rivals can still exist. The review therefore reports a finite-rival result, not universal induction.

## D6 — Keep the construction finite and transparent

**Choice.** Use small fixed offset templates with D4 transforms rather than a rejection sampler.

**Alternatives rejected.** Rejection-based random cells, which make exact controls and lesson guarantees fragile; a much larger shape library unrelated to the semantic defect.

**Probe.** Self-check, distribution, diversity, override, and task tests all pass; generation is deterministic and does not mutate global RNG state.

**Failure mode/limit.** The finite vocabulary and pivot offset ±1 are learnable distribution restrictions. They are documented and should be expanded only if downstream training needs a wider geometric envelope.

## Native-ready parametric extension

The separate `workspace/parametric/` family adds one episode-fixed `mode`:
`all_sources` (the exact canonical Racket text), `nearest_color`, and
`farthest_color`. The alternatives rank individual source cells by Manhattan
distance from gray, bind the winning color, then point-reflect every source of
that color, including disconnected non-extremal cells. This color lookup is the
required A→intermediate→B dependency. The canonical generator, ledger, authority
pin and approval bytes remain unchanged.

The adapter supports 2–6 demos and 1–4 queries with independent deterministic
streams, identical inputs across settings, and four distinct query profiles.
Two constructive teaching scenes distinguish distance, color binding, pivot,
side, frequency and aggregate-distance rivals. The small profile is 7x9 with
six sources; the 30x30 profile contains 420 source cells spread across the full
lawful 29x29 antipodal footprint. Inputs always have blank reflected targets,
3–4 source colors, repeated colors and unambiguous, different extremal colors.

The initial self-audit found an actual gap: the protected DSL's integer division
made two mean-distance scores tie, allowing an integer-mean selector to fit a
two-demo seed-0 lesson and miss its query. The second teaching scene now gives
means 6.25 versus 5.4 (integer scores 6 versus 5), while the required farthest
color has the larger individual distance. Exact and integer mean/centroid
rivals are now separate executable checks. The retained source-bound
pre-repair lesson is `workspace/parametric/evidence/integer-mean-counterexample.json`;
the corrected audit is `workspace/parametric/evidence/final-audit/`.

Measured current evidence:

- All 38 task tests pass, including 13 focused parametric tests. Strict counts,
  types, conflicting extrema, deterministic split independence, no grid aliasing,
  public-byte projection and the integer-mean regression are covered.
- The bounded self-audit passes 18/18 episodes: seeds 0 and 17, demo counts 2,
  3 and 6, all three settings and four queries. Its 672 protected Racket
  executions found no surviving declared rival with a different query answer.
  All audited 30x30 inputs have 420 sources and actual 29x29 content extent.
- The native inventory binds 29 files. Qualification passes all three settings
  over two seeds (six jobs, 78 Racket evaluations, 42 labeled pairs) at three
  demos and four queries. Returned receipts are under
  `checks/38200022d1b7/qualification/`.
- Two source-bound causal cases replace the Manhattan-selected color with the
  Euclidean-selected color. Both actual and counterfactual outputs execute and
  replay through protected Racket, and each counterfactual changes the copied
  pattern. Receipts are under `checks/38200022d1b7/causal/`.

The reusable audit and materializer are documented in the prototype README.
Public files reveal exactly one query input, with no settings, reference code,
query labels, later inputs, count or final-turn hints. Their names hash their
exact visible bytes; one-query and four-query first turns are identical.
Sequencing remains the consumer's responsibility. The two teaching templates
and four query profiles are finite distribution restrictions. Qualification
and rival rejection do not prove universal identifiability or training benefit.
Status is reviewer **ready**; owner acceptance of the integrated exact source
and any training admission remain separate.
