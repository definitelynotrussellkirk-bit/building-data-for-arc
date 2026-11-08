# Working notes: 31a4112b4151

## 2026-09-28 review: spatial bank and lesson identifiability

- Root cause: `_candidate_layouts` enumerated row-major and returned after a global 256 layouts. For the fixed 12×12 / four-target / canonical-corner / no-clipping case, all 128 sampled seeds used prototype origin `(0,0)` even though every standard battery stage was green.
- Repair: retain up to four deterministic target sets per feasible prototype origin, with 64 stable proposals and an exhaustive one-layout fallback. The same probe now has 80 unique origins spanning rows and columns 0–10.
- Follow-on regression found by the strict after semantic gate: changing deterministic draws exposed a four-demo lesson with only two targets in every demo, so `first_extra_target_only` survived. One slot per four-example window now uses 3+ targets and requires an omitted target to add visible output.
- Coverage: 864 ordinary configuration combinations and 288 evidence-rich teaching combinations had zero empty layout banks; 192 stressed lesson windows had zero identifiability failures.
- Rule decision: no Racket edit. `RULE_HASH=1c0487137cc2` remains pinned and canonical parity was already exact.
- Future check: after changing profiles, target counts, layout-bank constants, or `VERSION`, rerun the fixed spatial probe, full configuration census, exact failing lesson replay, and strict after semantic gate.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a306bda8d3bcb161da5aba6a4a87bce60389b51b1338f02e108a9be127550874`.

# Decisions for `31a4112b4151`

## Decision summary

I kept the selected Racket rule and the task's semantic grammar unchanged. I changed how lawful layouts are sampled and strengthened the four-example curriculum guarantee:

1. replace the global row-major 256-layout prefix with a deterministic, spatially balanced per-origin bank;
2. retain an exhaustive one-layout fallback for exact override support;
3. reserve one slot in every four-demo window for a 3+ target scene that visibly disproves “stamp only the first extra target”; and
4. classify the existing semantic predicates honestly as positive branch witnesses.

The generator version moves from `3.0.0` to `3.1.0`.

## Input choices and rationale

### Grid height and width: 7–12, unchanged

**Original rationale:** not explicitly recorded beyond coverage of canonical 9×9-scale examples and multiple clipping opportunities. Prior evidence deliberately included canonical-scale hard examples.

**Decision:** retain the full 7–12 override domain and existing difficulty weighting. The defect was not the dimension range; it was conditional placement support inside a fixed dimension.

**Alternatives rejected:** narrowing to canonical dimensions would reduce geometric diversity; expanding beyond 12 would add compute and clipping regimes without evidence that they improve this rule family.

### Template profiles: eight fixed connected shapes of size 3–6, unchanged

**Original rationale:** prior note `arbitrary_anchored_prototype_grammar` records the need to cover the canonical three-cell corner, four-cell cross, touching targets, and variable connected shapes rather than one fixture.

**Decision:** keep all eight current profiles and their sample-index schedule. They already cover sizes 3–6 and the canonical profiles, and all profile witnesses fired in the baseline.

**Limitation:** this remains a finite profile family, not uniform sampling over all connected polyominoes of size 3–6. Adding profiles should be driven by a concrete shortcut or canonical gap, not shape count alone.

### Template color: 1–8, unchanged

**Original rationale:** color 0 is background and color 9 is the anchor/target marker; all other ARC colors are semantically interchangeable template colors.

**Decision:** retain exact override support over 1–8. No color-specific skew or rule ambiguity was found.

### Number of color-9 targets: 2–4, domain unchanged; curriculum strengthened

**Original rationale:** the canonical task requires multiple targets, and prior design used 2–4 to vary output multiplicity.

**Observed failure:** after the layout repair changed deterministic draws, one pinned medium lesson happened to have only two targets in all four demos and three in the query. The wrong rule `first_extra_target_only` therefore fit every demonstration.

**Decision:** when `n_anchors` is not explicitly overridden, sample indices congruent to 2 modulo the four-demo lesson length draw only 3 or 4 targets. Candidate layouts for this teaching slot must also ensure that targets after the first extra contribute at least one output coordinate not already covered by the origin and first extra. Exact `n_anchors=2` overrides remain valid.

**Alternatives rejected:** weakening/removing the rival check would hide a real ambiguity; merely increasing the probability of 3+ targets would remain seed-dependent; forcing 3+ targets in every example would unnecessarily erase the useful two-target branch.

### Touching versus isolated targets: schedule unchanged

**Original rationale:** prior note `deterministic_branch_curriculum` records that independent random examples could miss the touching-target branch, so sample index schedules both touching and isolated cases.

**Decision:** retain `sample_index % 3 == 1` for touching and isolated otherwise. The candidate-bank repair preserves this constraint exactly.

### Partial clipping versus all-in-bounds: schedule unchanged

**Original rationale:** clipping is part of the selected rule and must be demonstrated explicitly.

**Decision:** retain alternating partial/no-clipping profiles. The new per-origin bank checks clipping status before accepting a layout, and all clipping witnesses remain covered.

### Prototype-origin and extra-target placement: changed

**Original rationale:** prior note `cached_exact_layout_enumeration` chose cached enumeration because exact grid size, target count, touching, and clipping combinations made per-call rejection sampling brittle. The implementation then imposed a global `256` cap for cost control.

**Observed failure:** enumeration was row-major and returned immediately at 256 layouts. In the 12×12, four-target, no-clipping canonical-corner profile, every retained layout used prototype origin `(0,0)`. Across 128 seeds, origin support was 1/128 unique positions, entirely in the top-left quadrant.

**Decision:** enumerate every feasible prototype origin, then use a stable task/version/config/origin RNG to retain up to four lawful target sets for that origin, trying at most 64 random proposals. If an origin has no accepted proposal, run a deterministic exhaustive search until one lawful layout is found. This preserves deterministic replay and exact overrides while preventing an early origin from consuming the whole bank.

**Why four layouts per origin:** it gives target-placement variation without letting origins with combinatorially many target sets dominate origin probability. It also bounds cache size.

**Alternatives rejected:**

- **Raise the global cap:** postpones but does not remove row-major prefix bias.
- **Shuffle a fully enumerated global list:** still requires materializing the combinatorial list and gives origins with more target combinations greater mass.
- **Pure per-call rejection sampling:** reintroduces brittle exact overrides and repeated work.
- **One layout per origin only:** fixes position support but unnecessarily collapses target-set variation.
- **Change the Racket rule:** all canonical pairs, rule hash, authority sync, and Python/Racket parity were already correct; no rule defect justified churn.

### Semantic witness declarations: metadata strengthened

The seven existing predicates measure positive branches (shape sizes, touching/isolation, clipping/no clipping, and 3+ targets). They do not honestly claim that every individual firing refutes a named rival. I therefore declared them as `BRANCH_WITNESSES`; the stronger context-dependent claims remain in `lesson_identifiable`.

## Probes and evidence

- Baseline battery: 12/12 stages green.
- Fixed stress case before repair: 128/128 origins at `(0,0)`; one unique origin; only top-left quadrant.
- Same stress case after repair: 80 unique origins; row and column span 0–10; quadrant counts 39/31/33/25.
- Ordinary configuration census: all 864 combinations of 7–12 dimensions, eight profiles, and 2–4 targets had at least one lawful layout; origin support ranged 19–121.
- Evidence-rich teaching census: all 288 tested dimension/profile/touch/target-count combinations had lawful layouts; origin support ranged 23–110.
- Lesson stress: 192 four-demo windows across all bands had zero identifiability failures.
- Focused tests include the exact semantic-gate replay and the fixed-override spatial collapse repro.

Evidence files: `checks/31a4112b4151_spatial_distribution.json`, `checks/31a4112b4151_configuration_census.json`, and the before/after battery directories.

## Failure modes and limitations

- The per-origin bank is balanced over feasible origins, not uniform over every legal full layout. Up to four target sets per origin are retained.
- Origins with fewer than four feasible accepted sets can have slightly less mass than origins with four; the catastrophic row-major collapse is removed, but exact uniformity is not claimed.
- The 64 randomized proposals are backed by exhaustive fallback for existence, but the fallback retains only the first lawful target set for that origin.
- The eight shape profiles remain finite and can still leave an unmodeled shape-specific shortcut.
- Ordinary curriculum scheduling guarantees all-target evidence, but a caller explicitly overriding `n_anchors=2` can intentionally request a two-target example that cannot by itself refute `first_extra_target_only`.
- Version changes reseed ordinary `gen_ctx` draws. The new tests guard the semantic lesson property rather than relying on one previously lucky seed population.
- Training-safe approval still requires independent intake/replay; this return is a candidate change, not self-approval.

## Parametric family review — 2026-10-25

**Decision:** retain the reviewed production generator and exact canonical rule, and add a task-local episode parameter `target_scope = all_targets | clipped_targets`. The default `all_targets` program is byte-identical to canonical SHA-256 `1c0487137cc2e705905e238b7cd76fd074b74331fefc0de8c9d1ed0107e5888f`. The alternative extracts the input prototype, uses those offsets to select exactly the color-9 targets whose copied shape would cross the boundary, and stamps only that selected set.

**Teaching design:** every retained scene contains two clipped and two unclipped targets, at least two clipped destinations, matched inputs across settings, independently selectable 2–6 demonstrations, and four distinct queries. The fourth query is a distributed 30×30 case with a 5–6-cell prototype. A 128-episode audit found no harmful demonstration-only survivor among six named shortcuts.

**Repair made during staging:** the existing test `test_generator_31a4112b4151.py` resolved canonical data through a source-tree-relative hard-coded path and failed in the staged runtime. It now uses `reviewer_support.find_root` plus `canonical_path`; the final task suite passes 47/47.

**Evidence and limits:** authoring preflight passed 4 source-bound jobs and 40 protected-Racket evaluations; the wrong-intermediate witness changed the final output; 16 public one-query views passed 24 private-field invariance checks and 4 positive controls. These are finite reviewer checks, not owner qualification, acceptance, or training admission. The next action is owner integration followed by native exact-source qualification and fresh acceptance.

