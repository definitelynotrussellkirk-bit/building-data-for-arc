# Working notes: 92f4d4eb0dbb

## Provenance and authority

- Assigned baseline: generator v3.0.0, SHA-256 `85b41f2534e93c574a2a4ad61971f6d1b0e784f4e98f1ecf238bd067d708d421`.
- Final generator: v3.1.0, SHA-256 `c71752cd690b3548856be0b1927f7381b245ab2009542f27e49b0d15ba540dda`.
- Canonical Racket authority remains unchanged and pinned by `RULE_HASH = "5e129c41777b"`.
- The prior return `review-8d5a080a5456928f:v0001` was used only as a lead. Its unresolved audit identified a pixel-centroid support gap on the v3.0.0 morphology bank; all claims below were freshly measured on v3.1.0.

## Intended rule

Find the minimum and maximum rows containing color 1. Recolor a color-1 cell to color 2 exactly when its row is strictly below the occupied-row bounding-box midpoint, equivalently when `2 * row > min_row + max_row`. Preserve every other cell.

## Baseline diagnosis

The completed before battery had 11 green stages and one failed stage, `defect_lint`. It produced 30 strict-scalar warnings because `generate()` accepted non-exact-integer seeds and invalid `difficulty` values. Baseline task tests were 56/56 green.

The stronger semantic defect was a support gap rather than a wrong label: all four emitted morphologies had row occupancies symmetric around their bounding-box midpoint. Therefore the plausible rival “split at the mean row of the color-1 pixels” was answer-equivalent on all production support even though it differs on lawful asymmetric shapes. The retained prior audit supplied a hand-built lead; this repair adds generated support and fresh source-bound evidence.

## Repair implemented in v3.1.0

1. Added exact call-scalar validation. `seed` and `sample_index` must be exact integers, `sample_index` must be nonnegative, and `difficulty` must be `None`, `easy`, `medium`, or `hard`.
2. Added `notched_frame`, a frame with the bottom middle cell removed. This keeps the occupied bounding box unchanged while shifting the pixel centroid.
3. Changed both odd schedule profiles to emit `notched_frame` by default. Every consecutive three-demonstration production lesson therefore contains a generated witness against both the inclusive-midpoint and pixel-centroid rivals.
4. Added an independent `pixel_centroid` oracle to the task workspace and declared it in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.
5. Added a `bounding_box_midpoint` semantic witness and mapped it to the centroid rival.
6. Retained the original four-position schedule, canonical-scale support, free placement/reflection, exact observable axes, and unchanged Racket authority.

The minimal generated witness is `counterexamples/pixel-centroid-generated-witness.json`: seed 0, sample index 1, easy, no overrides, observed as a 9×11 span-5 `notched_frame`. It passes `self_check`, the selected Racket output matches the independent intended mirror, and the centroid rival changes two middle-region cells too early.

## Test-driven evidence

The scalar and centroid regressions were written before implementation. The first generator run failed 21 tests as expected; a later independent-probe run exposed five additional failures because the workspace observer did not yet recognize `notched_frame`. That observer was repaired rather than weakening the assertions.

Final measured evidence:

- Task-local portable tests: **85/85 passed** in `checks/task-tests-after/`.
- Strict after battery: **12/12 stages green** in `checks/after-final/`.
- Profile floor: 30/60 exact canonical-profile hits and 40/60 canonical-envelope hits; every band had exact support and zero crashes.
- Override matrix: 21,060/21,060 accepted draws, zero findings or warnings; all four axes were exhaustive over their declared domains.
- Semantic smoke gate: 12/12 three-demo lessons identifiable and 48/48 query rotations unambiguous against declared rivals.
- Large lesson census: **300/300** production lessons and **1,200/1,200** query rotations had no ambiguity, with 1,200 Racket-labelled pairs and 735 unique inputs (`checks/lesson-census-final.json`).
- Generated centroid witness frequency in the semantic gate was 292/600 draws across all three bands.
- Post-repair visible-only solve: first hypothesis passed 3/3 demonstrations; earlier rule exposure was declared `yes`, reference consultation during solve `no`.

## Parametric extension assessment

A separate runnable proposal lives under `workspace/parametric/`. It preserves the original reasoning pattern and canonical default while varying two bounded episode-level parameters:

- `side`: `lower` (canonical) or `upper`;
- `boundary`: `strict` (canonical) or `inclusive`.

One setting is chosen once for all three demonstrations and the query. Prototype inputs have odd occupied height, an occupied midpoint row, and occupied cells on both strict sides, so all four settings differ on every pair. Exact Racket verification covered four retained episodes and 16 unique inputs: all stored outputs matched Racket, every rival Racket program matched its Python mirror, every rival was refuted by every demonstration, and every query was setting-sensitive. Evidence: `checks/parametric/92f4d4eb0dbb-midpoint.json` and `workspace/parametric/evidence/manifest.json`.

This remains a proposed task-local extension. It is not selected, does not alter the catalog rule, and does not establish all-seed behavior.

## Decisions and reversals

### D1 — Keep the canonical authority unchanged

The observed problems were input-contract and teaching-support defects, not evidence that the Racket rule was wrong. Changing the rule would have broken authority synchronization without solving the sampler gap.

### D2 — Reverse the “balanced morphologies only” support choice

**Prior choice:** frame, ladder, diamond, and zigzag all had symmetric row occupancy. This made the pixel-centroid rival impossible to distinguish on generated inputs.

**New choice:** add a one-cell bottom notch and place it on every odd schedule profile. The change is minimal, remains connected and structurally lawful, preserves the same object role and midpoint reasoning, and supplies a production witness in every three-demo schedule window.

### D3 — Retain the four-position curriculum schedule

The existing canonical-even / canonical-odd / broad-even / broad-odd cycle already guaranteed an odd-height witness in every three consecutive examples. Reusing that schedule and strengthening the odd morphology was smaller and more auditable than adding resampling or a longer schedule.

### D4 — Declare both strongest known rivals

The inclusive-midpoint rival distinguishes strictness; the pixel-centroid rival distinguishes which notion of center is used. Lessons now explicitly refute both. This is still a finite rival set, not a proof of unique induction against every conceivable hypothesis.

### D5 — Keep parametric variants separate

The `side × boundary` prototype is useful because the parameters are small, compositional, and demonstrably teachable. It remains outside production so accepting the generator repair cannot accidentally approve four new rule variants.

## Remaining limitations and open status

- The production sampler still uses colors 0/1, recolors to 2, and uses five-column generated morphologies with occupied heights 5–7; the validator accepts a somewhat wider structural envelope.
- The 300-lesson census is random source-bound evidence, not an exhaustive proof over all seeds or undeclared rivals. The schedule period is not formally declared, so no schedule-period enumeration claim is made.
- Generic measured label mutations reported as support-equivalent are not task-semantic alternatives; the declared midpoint rivals are the reviewed task-specific hypotheses.
- The prior centroid audit remains formally unresolved in `evidence/review_index.json` until maintainer intake. This return supplies a concrete repair and verification but does not self-close historical findings or grant training approval.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-8d5a080a5456928f:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `85b41f2534e93c574a2a4ad61971f6d1b0e784f4e98f1ecf238bd067d708d421`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit resolution of centroid support gap on accepted c71752cd690b3548856be0b1927f7381b245ab2009542f27e49b0d15ba540dda. Odd default profiles now generate notched_frame, with retained ordinary seed0/index1/easy Racket witness. Independent centroid rival/witness declarations and focused cyclic-start tests cover all4 starts across None/easy/medium/hard; reviewer-reported85/85 task tests plus fresh85/85 and300 lessons/1200 rotations pass against both declared midpoint rivals. Evidence: counterexamples/pixel-centroid-generated-witness.json and checks/selected-counterexample/racket.json from review-5b916a89fc2e7265. Old audited source 85b41f2534e93c574a2a4ad61971f6d1b0e784f4e98f1ecf238bd067d708d421. No owner task rerun; finite two-rival evidence only.

### Assessment or prior finding

## 92f4d4eb0dbb

**A1 — Possible shortcut / teaching-support gap: pixel centroid is indistinguishable on the entire emitted morphology bank.** The rival recolors color-1 cells strictly below the mean row of all color-1 pixels, whereas the selected rule uses the occupied bounding-box midpoint. Every source morphology has palindromic row occupancies (the zigzag has exactly two cells per row), so their centroids equal their bounding-box midpoints. Horizontal reflection, lawful placement, canvas dimensions and difficulty preserve that equality. See `generators/92f4d4eb0dbb/generator.py:155–217`; the sole declared competitor at lines 388–412 tests midpoint inclusivity, not the choice of center.

Fresh selected-Racket evidence confirms that the centroid rival fits **4/4 canonical pairs and 48/48 generated inputs**, including all 12 morphology/span combinations. Generated sampling was seed **0**, indices **0–15** in each of **easy, medium, hard**, with **no overrides**; these 48 draws contain **32 unique inputs**. This bounded execution check supports the separate source argument that no currently emitted shape can refute the rival.

**Separating witness.** `checks/audit/92f4d4eb0dbb/input.json`, input index **52**, is a hand-built **7 rows × 7 columns** frame spanning rows/columns 1–5, with the bottom cell **(5,3)** removed. Output is also **7 rows × 7 columns**. The bounding-box midpoint remains **3**, while the pixel centroid becomes **43/15**. Actual Racket output keeps **(3,1)** and **(3,5)** at color **1**; the centroid rival incorrectly changes both to **2**. Both `self_check` and `strict_canonical_like` return `[]`. The fixture belongs to the documented structural validator domain, but **is outside the current four-template sampler support**; its seed/index/overrides are null because it is hand-built. This is a possible shortcut and coverage concern, with **no generated-label mismatch or production-query ambiguity claimed**. Full input, actual Racket output and rival output are in `evidence.json` under `counterexample`.

**Lesson checks and scope.** All 53 retained inputs pass both validators and obtain valid, error-free Racket outputs; the independent bounding-box mirror matches **53/53**. The actual declared `CANONICAL_SHORTCUTS` map was iterated: `inclusive_midpoint` fits all **4/4** canonical pairs. Reusing the 48 generated pairs, **39 overlapping ordered lessons** (three consecutive demonstrations, fourth pair queried; starts 0–12 per band) and **156 rotated assemblies** (query positions 0–3, including the original position) pass the declared lesson contract. The centroid rival survives every pair and query in those assemblies: it is answer-equivalent on that sampled support, with **zero within-support query ambiguities**. No full battery or task-test suite was run for this audit.

**Suggested direction.** Add a lawful shape with asymmetric row occupancies, such as the retained one-cell deletion, and an executable centroid competitor if the lessons should teach the bounding-box rule throughout the validator domain. Ensure a complete lesson exposes the distinction. If the intended training domain is restricted to balanced row occupancies, document that narrower teaching claim explicitly.

**Source and evidence.** The audited generator is unchanged SHA-256 `85b41f2534e93c574a2a4ad61971f6d1b0e784f4e98f1ecf238bd067d708d421`, version `3.0.0`. Executed rule ID is `5e129c41777b`; the public apply receipt records executed rule-text SHA-256 `94b1a1a1024aca3f9324be521db8e881f9bb39150f0b7cf2d7bd7f84775f3b68`. Canonical raw-text SHA-256 is `a839a1913d6e0a0bdb39fbff4e9e38f926d9f3c59ee7627dc9c9eb929dd71d6f`; full whitespace-normalized rule SHA-256 is `5e129c41777b021dcdd151d210514f0ba4330a6f65ade7919acaa5e12cff70eb`. The original current review index has no audit rows and a reviewer-reported decision bound to these generator bytes. Its inherited 56-test, 12-stage and 300-lesson claims were read, not rerun or promoted into fresh audit evidence. No approval or resolution is claimed.

Reproduce with the three exit-0 commands in `checks/audit/92f4d4eb0dbb/commands.json`, all invoked from `packet_root` with effective payload cwd `WORK/repo`. The reusable probe is `checks/audit/92f4d4eb0dbb/reproduce.py`; retained inputs/provenance are `input.json` and `cases.json`, actual authority output is `racket.json`, and source-bound analysis is `evidence.json`, all in that same audit directory. The Racket command was:

```bash
python3 review.py run python3 -m arcpuzzles apply 92f4d4eb0dbb --input ../checks/audit/92f4d4eb0dbb/input.json --out ../checks/audit/92f4d4eb0dbb/racket.json
```

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-8d5a080a5456928f-v0001/audit_assets.json), manifest SHA-256 `0806dffd7923866f68642031b1c27912e7203ee06fc2bbf021a8686ade2409ea`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `c71752cd690b3548856be0b1927f7381b245ab2009542f27e49b0d15ba540dda`.

# Decisions

## D1 — Preserve the canonical Racket authority

**Choice.** Keep the selected Racket source, canonical examples, and `RULE_HASH = "5e129c41777b"` unchanged.

**Rationale.** Fresh evidence located the faults in Python call validation and generated teaching support. The selected authority correctly labelled the new asymmetric witness, and the final authority-sync and execution-parity gates passed. A rule edit would have changed the task rather than repairing the generator.

**Alternatives rejected.** Relabelling the task around the pixel centroid, changing the threshold convention, or refreshing an approval hash were all rejected because no authoritative-label defect was found.

**Failure mode retained.** Future evidence could still reveal a reference defect outside the measured domain; this return does not claim otherwise.

## D2 — Reject invalid call scalars at the source

**Choice.** Require `type(seed) is int`, `type(sample_index) is int and sample_index >= 0`, and `difficulty` to be exactly `None`, `easy`, `medium`, or `hard`.

**Prior behavior.** The baseline accepted booleans, floats, numeric strings, and invalid difficulty scalars. The original rationale for permissiveness is unknown.

**Rationale.** These are public call arguments, not fuzzy input features. Silent coercion or acceptance makes deterministic generation and source-bound replay ambiguous. The strict battery specifically treats these warnings as blockers.

**Alternatives rejected.** Coercing with `int(...)`, accepting arbitrary strings as difficulty, or validating only inside `gen_ctx` would preserve ambiguous semantics and would not fix the measured lint finding.

**Probe.** `checks/tdd-red-generator.log` records the failing tests; `checks/after-final/checks/92f4d4eb0dbb_after_defect_lint.log` records the final clean result.

## D3 — Add a minimal asymmetric morphology

**Choice.** Add `notched_frame`: the existing five-column frame with only its bottom-middle cell removed.

**Prior choice.** The v3.0 bank contained `frame`, `ladder`, `diamond`, and `zigzag`. All happened to be row-balanced. Their original rationale appears to have been visual diversity, but no retained note justifies the symmetry itself; that rationale is therefore unknown.

**Rationale.** The one-cell notch preserves the task's object role, occupied bounding box, connectedness, non-solidity, colors, placement freedoms, and midpoint reasoning while separating the occupied-bounding-box midpoint from the pixel centroid. It is a smaller semantic change than inventing a new object family.

**Alternatives rejected.** A hand-built validator-only witness would not teach production lessons. Randomly sampling a rare asymmetric shape would leave many lessons ambiguous. Resampling until a witness appears would make schedule behavior less transparent and harder to replay. Deleting a side cell was rejected because it can change width or create reflection-dependent observability.

**Probe.** The source-bound generated case is `counterexamples/pixel-centroid-generated-witness.json`; the actual Racket result is `checks/selected-counterexample/racket.json`.

## D4 — Put the witness on both odd schedule profiles

**Choice.** Retain the four profiles `canonical_even`, `canonical_odd`, `broad_even`, `broad_odd`, and use `notched_frame` as the default morphology for both odd profiles. Even profiles continue cycling through the four balanced kinds.

**Rationale.** `EXAMPLES_NEEDED = 3`; every length-three window of a four-position cycle contains an odd profile. This supplies a centroid witness and a strict-vs-inclusive midpoint witness in every complete lesson while preserving the existing canonical/broad and even/odd curriculum structure.

**Alternatives rejected.** Lengthening the cycle, increasing the demonstration count, or injecting seed-dependent witness resampling would increase complexity without improving the measured teaching guarantee. Making every profile notched would unnecessarily reduce diversity.

**Probe.** Focused tests exhaust all four cyclic starts under all four difficulty contexts. The semantic gate observed 292 witness hits in 600 draws, and the large census found no declared-rival ambiguity in 300 production lessons or 1,200 query rotations.

**Known restriction.** Odd profile identity is now visually correlated with the notched morphology. This makes the schedule easier to infer but does not determine output labels without applying the midpoint rule.

## D5 — Declare the strongest task-specific rivals explicitly

**Choice.** Retain `inclusive_midpoint` and add an independent `pixel_centroid` oracle to `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`. Add semantic witnesses `strict_midpoint` and `bounding_box_midpoint`.

**Rationale.** The first rival tests threshold strictness. The second tests which notion of center is used. Both fit all usable canonical demonstrations, so both must be teachably false on generated demonstrations rather than merely documented in prose.

**Alternatives rejected.** Using the production transform itself as the rival oracle would not be independent. Naming a rival without executable output or a source-bound counterexample would not support the semantic gate.

**Limit.** This is a finite reviewed rival set. Generic label mutations and all conceivable human hypotheses remain outside the claim.

## D6 — Preserve and exhaust the existing exact axes

**Choice.** Keep exact axes `grid_h=7..14`, `grid_w=7..14`, `span=5..7`, and `shape_kind` expanded to five values. Keep no incompatible combinations because every advertised combination is constructively valid.

**Rationale.** The repair did not require changing canvas or span ranges. Exact controls are useful for curriculum authoring only when every value is observable and honored. The final override matrix exercised 234 cases across three bands and 30 seeds per case: 21,060/21,060 accepted, zero findings/warnings.

**Alternatives rejected.** Hiding `notched_frame` from overrides would make it difficult to reproduce. Declaring fake incompatibilities to reduce testing would weaken the contract.

## D7 — Keep the parametric extension separate from production

**Choice.** Build a task-local `side × boundary` prototype with canonical default `lower + strict` and values selected once per episode.

**Why these parameters.** Both alter executed semantics while preserving the original reasoning decomposition: identify occupied row bounds, derive the midpoint, choose a side, apply strict or inclusive comparison, recolor only color-1 cells. They are small and jointly interpretable rather than cosmetic reskins.

**Input constraints.** Prototype episodes use odd occupied height, an occupied midpoint row, and occupied cells on both strict sides. Those constraints are deliberate teaching support: all four settings differ on every retained pair.

**Alternatives rejected.** Color parameters were rejected as mostly cosmetic. Canvas size, placement, reflection, and morphology are input-distribution parameters rather than rule parameters. A free threshold offset was rejected because it expands the hypothesis space and can make settings indistinguishable on small shapes.

**Status and evidence.** `proposed_prototype_not_selected`; four settings, 16 unique inputs, exact Racket programs and public/complete episodes. See `checks/parametric/92f4d4eb0dbb-midpoint.json`. This does not claim catalog integration or all-seed validation.

## D8 — Use a task-local verifier workaround, not a shared-source edit

**Choice.** `workspace/parametric/verify.py` extracts the known retained rule bodies and reuses one Racket bridge for all comparisons.

**Rationale.** The packet's stripped `puzzle_generators.rule_wrap.wrap_rule` imports `scripts.comment_solutions`, but `scripts` is absent. Repeated bridge startup also exceeded the practical verification limit. A single bridge gives exact Racket evidence efficiently without editing shared files outside the allowed task scope.

**Alternative rejected.** Copying the missing parser into this generator would duplicate shared infrastructure and conceal the packaging defect. The shared fix is proposed as F1 instead.

## D9 — Evidence and stopping rule

**Choice.** Stop after the final portable tests, strict battery, standalone lint, exact prototype verification, generated Racket counterexample, 300-lesson rotation census, post-repair visible-only solve, and two required audits were complete.

**Rationale.** All required gates are green on one final generator hash, and the remaining caveats are finite-evidence limits rather than a concrete failing case in the repaired generator.

**Not claimed.** Universal identifiability, exhaustive all-seed coverage, closure of historical review-index findings, approval of the parametric variants, or training admission.
