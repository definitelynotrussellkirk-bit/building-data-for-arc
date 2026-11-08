# Current notes: e03758508612

## Intended rule

Row 0 columns 0–2 are a left-to-right priority legend. Cyan (`8`) walls below the legend divide the canvas into two, three, or four rectangular chambers. Each chamber contains one or two legend-colour seeds, and the authoritative output fills the chamber with the earliest legend colour present while preserving legend and walls. The canonical Racket authority remains unchanged at declared rule hash `d93ad16a99ae`.

## Reversed distribution decision

Version 2.2.0 generated only four equal 2×2 midpoint chambers and advertised several aliases/degenerates that were not lawful exact controls. That choice made wall parsing unnecessary: a fixed midpoint-quadrant rival matched the generated family, while `self_check` rejected three of four canonical layouts. Version 3.0.0 replaces it with an eight-slot schedule covering canonical 2-room, 3-room, unequal 2-room, and 4-room profiles plus broader rectangular layouts; evidence is in `checks/before/`, `checks/after/`, and `checks/lesson-census.summary.json`.

## Current controls and assumptions

The only advertised exact controls are `grid_h` (8..14), `grid_w` (9..17), `layout` (`horizontal`, `vertical`, `grid`), and `seed_pattern` (`single`, `mixed`, `double`). Overrides are strict and observable from pixels; unknown keys, non-integer/bool seeds, negative/non-integer sample indices, and unknown difficulty labels are rejected. The selected domain is deliberately rectangular and cyan-walled, with exactly three distinct legend colours and one or two seeds per chamber.

## Teaching contract

Declared rivals are `midpoint_partition` and `lowest_priority`. Production lessons use three demonstrations and one query; each lesson must refute both rivals. The final 100-per-band census found 300/300 identifiable production lessons and 1,200/1,200 identifiable held-out-query rotations, with 1,200 unique inputs and no materialization or scoring errors.

## Retained counterexample and tests

`counterexamples/midpoint-rival-generated.json` is a generated unequal-layout witness on which the midpoint rival disagrees with the canonical rule. Task-local tests cover canonical examples, schedule/profile support, exact overrides, invalid calls, rival witnesses, the retained counterexample, and the isolated priority-direction prototype.

## Parametric prototype

`workspace/parametric/` contains a proposed episode-level `priority_direction` parameter (`left_to_right` or `right_to_left`) with separate exact Racket programs and public examples. It is intentionally not wired into canonical generation; the canonical default remains left-to-right. Seed-17 evidence shows both settings match their Racket program and every demonstration distinguishes the opposite setting.

## Known limits and open findings

This is a finite declared-rival audit, not a proof of unique induction. Generation does not cover irregular or nested chambers, more than four chambers, more than two seeds per chamber, non-cyan walls, or variable legend length. No repair blocker remains; training admission remains a maintainer decision outside this review.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d0679c3a03db9377:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `390ce9fc2493f3da44269562c961bed54e912ea1af4cfdee148dd6f5af951585`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused closure against current c398a044b92905869a95f0037479cfbabf8edbba426dd9d8f63d155d65f9cc4e. Owner static inspection confirms horizontal/vertical/grid layouts2..4rooms andunequalpartitions replaceoldfixedmidpoints;midpoint_partition rivaldeclared andtestscovernonmidpointlayouts plusretainedmidpoint-rival-generated.json withRacket/rivaldisagreement. Reviewer current-source60tests and300lessons/1200rotationsfocusdirectlyonthepriorwall-parsing shortcut;finite rectangular/schedule limitsremain.

### Assessment or prior finding

## e03758508612

**Reproduced teaching shortcut: fixed midpoint partitions replace wall parsing.** The selected generator always builds four equal rectangular rooms as a 2×2 arrangement. A rival that groups non-wall cells solely by `row >= height // 2` and `column >= width // 2`, picks each group's highest-priority seed, and preserves cyan pixels agrees with the reference on this generated family. It never uses wall placement or connectivity to choose a room. The selected Racket rule instead flood-fills the connected regions below the legend. Its canonical examples include two horizontal rooms and three vertical rooms, so this distribution restriction drops an intended reasoning step.

**Source binding:** generator version `2.2.0`, SHA-256 `390ce9fc2493f3da44269562c961bed54e912ea1af4cfdee148dd6f5af951585`; canonical selected rule hash `d93ad16a99ae`. The supported `arcpuzzles apply` receipts confirm the executed rule matches that catalog hash and the generator hash. Current task notes are placeholders, associated notes are empty, and no `evidence/review_index.json` exists for this target; no pre-existing resolution was available.

**Accepted counterexample:** start with `generate(seed=17, sample_index=3, difficulty="easy", **{})`, an 8×11 grid with legend `[6,7,2]`. Move the internal vertical divider from column 5 to column 6 on rows 2, 3, 5, and 6: change `(r,5)` from 8 to 0 and `(r,6)` from 0 to 8 for those four rows, preserving every seed and all horizontal/outer walls. The selected generator's actual `self_check(..., difficulty="easy")` returns `[]`. The public canonical Racket execution succeeds. The rival predicts 7 at `(2,5)` and `(3,5)`; Racket paints both 6 because they now belong to the top-left room. The accepted counterfactual input SHA-256 is `9908a3b1b6122e82a4860c6a7e21ba8595ffe55bfa1e3355f2887ac7dde00b12`. This is explicitly a hand-made accepted counterfactual, not a claim that unmodified generation reaches it.

**Focused checks:** 12 original generated inputs (`seed=17`, actual sample indices `0,1,2,3` in each of `easy`, `medium`, and `hard`, overrides `{}`) all passed `self_check` and the midpoint rival matched every selected Racket output. Universal agreement on unmodified generated inputs follows from the source's fixed divider construction (`row=ch+2=height//2`, `column=cw+1=width//2`), rather than from treating this small finite sample as exhaustive. On canonical variant 0, training pair index 3, the same rival differs from the authoritative output at 20 cells; that input is rejected by the current `self_check` with `expected 4 chambers below legend, got 2`. This last rejection is reported honestly and reinforces the narrowed generator domain; the shifted-divider witness above is independently accepted.

**Evidence and replay:** `checks/audit/e03758508612/reproduce.py` implements the rival, exact generation, mutation, admission assertions and Racket comparisons. `shifted-case.json`, `shifted-input.json`, `shifted-racket.json`, and `shifted-summary.json` retain the decisive accepted witness and labels. `canonical.json`, `cases.json`, `input.json`, `racket.json`, and `summary.json` retain the 12 generated comparisons and canonical two-room witness. `commands.json` records exact argument arrays, outer packet cwd, effective `WORK/repo` cwd, exit codes (all seven verification commands exited 0), source/rule identities and evidence paths. Run the listed `prepare`, public `apply`, and `verify` commands from the packet root; label output paths must be fresh because public `apply` refuses to overwrite.

**Disposition:** actionable source-bound finding; no selected sources changed. This audit establishes loss of wall parsing through fixed layout, not incorrect Racket labels on ordinary generated inputs. A future repair should vary divider locations, room counts and dimensions within the canonical rule's legal chamber domain, and explicitly refute this midpoint rival in exported lessons. No full battery or untested lesson-identifiability claim is made.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d0679c3a03db9377-v0001/audit_assets.json), manifest SHA-256 `52fcd3cd2ed4774732bcd42a182df7042ee405727e3f26582673129c981d0433`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `c398a044b92905869a95f0037479cfbabf8edbba426dd9d8f63d155d65f9cc4e`.

# Decisions for e03758508612

## D1: Preserve the canonical rule and repair the distribution

**Prior choice:** version 2.2.0 described the task as four equal 2×2 chambers. Its rationale beyond implementation convenience is unknown; the notes were a placeholder.
**Problem:** the canonical rule flood-fills wall-connected chambers, but fixed midpoint dividers made connectivity unnecessary and rejected canonical two- and three-room examples.
**Decision:** leave canonical Racket authority `d93ad16a99ae` unchanged and broaden only generator inputs.
**Alternatives rejected:** changing the rule to “four midpoint quadrants” would fit the old sampler but contradict canonical examples; retaining the sampler and adding only more random seeds would not restore wall parsing.
**Probe/evidence:** prior return `review-d0679c3a03db9377:v0001`, baseline battery, and `counterexamples/midpoint-rival-generated.json`.
**Failure mode/limit:** the selected family still covers rectangular rooms only.

## D2: Use an eight-slot schedule with canonical anchors

**Decision:** profiles 0–3 reproduce the four canonical height/width/colour-count profiles in every difficulty band; profiles 4–7 broaden geometry by band. `schedule_profile = sample_index % 8` is explicit and inspectable.
**Rationale:** deterministic anchors make strict profile support auditable, while the remaining slots avoid a canonical-only memorization distribution.
**Alternatives rejected:** unconstrained random dimensions had no guaranteed per-band profile floor; sampling only the four canonical profiles would have high support but poor geometric breadth.
**Probe/evidence:** `checks/after/checks/e03758508612_after_profile_floor.json` (33/60 exact, 40/60 envelope, support in all bands) and the 600-draw semantic schedule census.
**Failure mode/limit:** a model can infer the finite modulo-8 schedule if sample ordering leaks; lessons therefore rely on pixel evidence and rival checks, not hidden schedule secrecy.

## D3: Generate two, three, and four wall-connected chambers

**Decision:** support horizontal two-room, vertical two/three-room, and 2×2 four-room layouts, with room dimensions composed from legal canvas space. Broad profiles prefer unequal partitions where possible.
**Rationale:** this directly restores the connectivity step present in the authority and canonical examples.
**Alternatives rejected:** arbitrary irregular walls would broaden more but exceed the canonical rectangular evidence and complicate validation; fixed hand-authored templates would preserve a lookup shortcut.
**Probe/evidence:** final self-check, retained midpoint witness, semantic rivals, and 1,200 unique census inputs.
**Failure mode/limit:** no L-shaped, nested, diagonal, or more-than-four-room cases are generated.

## D4: Keep exactly three legend colours and one or two seeds per chamber

**Decision:** retain the rule-intrinsic three-cell legend and vary seed evidence with `single`, `mixed`, and `double` patterns. Double-seed cases cycle through all legend-priority pairings; mixed cases contain both one- and two-seed chambers.
**Rationale:** the task’s reasoning target is priority selection within a chamber, not legend-length induction. The patterns make priority relevant while preserving lawful canonical semantics.
**Alternatives rejected:** zero-seed/no-wall/no-legend “textures” are malformed counterfactuals, not exact production controls; three or more seeds add little because the legend has only three colours and canonical evidence supports one or two.
**Probe/evidence:** override gate, `observe_overrides`, and priority rival counts in the semantic gate/census.
**Failure mode/limit:** no variable legend length or repeated legend colour is tested.

## D5: Advertise only exact, observable controls

**Prior choice:** `ch_h`, `ch_w`, palette aliases, fixed singleton metadata axes, and degenerate `texture` values were advertised; several were dead, misleading, or produced self-check failures.
**Decision:** expose only `grid_h`, `grid_w`, `layout`, and `seed_pattern`; reject unknown keys; provide `observe_overrides` that recovers all four from pixels.
**Rationale:** every advertised intervention should have an observable contract, and malformed diagnostic cases should not masquerade as production axes.
**Alternatives rejected:** keeping aliases for backward compatibility would continue ambiguity; treating degenerates as “hard” examples would teach undefined tasks.
**Probe/evidence:** baseline override diagnostics versus final all-green override stage.
**Failure mode/limit:** some height/layout combinations are geometrically impossible and fail honestly rather than silently changing the requested value.

## D6: Validate scalar calls at the task boundary

**Decision:** require literal Python integers for seed/sample index, nonnegative sample index, and difficulty in `{None,easy,medium,hard}`. Bools are rejected even though Python subclasses `bool` from `int`.
**Rationale:** the strict defect detector showed that float/bool seeds and negative/non-integer indices were accepted, creating unstable provenance.
**Alternatives rejected:** coercion would collapse distinct invalid calls and hide caller defects.
**Probe/evidence:** 12 expected red tests in `checks/task-tests-red-scalar/result.json`, then passing final tests and defect lint.
**Failure mode/limit:** seed range is otherwise unbounded; that is intentional because the shared RNG accepts arbitrary integers.

## D7: Make shortcut hypotheses executable

**Decision:** declare `midpoint_partition` and `lowest_priority` in both semantic and lesson competitor contracts, with witness predicates and a retained generated counterexample. Require every three-demo lesson to refute both.
**Rationale:** correct labels are insufficient when demonstrations also support a cheaper wrong rule. Executable rivals convert this from prose review to repeatable training-data evidence.
**Alternatives rejected:** witness-frequency-only checks do not prove that a complete lesson distinguishes the rival; a generic diversity score does not target the observed failure.
**Probe/evidence:** 12-lesson smoke, 48 smoke rotations, and 100-per-band census with 1,200 required rotations.
**Failure mode/limit:** two declared rivals and generic mutations are not an exhaustive hypothesis class.

## D8: Keep `priority_direction` as an isolated prototype

**Decision:** build a separate episode-level parameter with two exact Racket programs, choose once from seed parity, and ensure every demonstration contains a two-colour priority conflict. Do not wire it into the canonical generator.
**Rationale:** direction is a small coherent rule parameter that can be inferred from demonstrations; it tests compositional rule variation without weakening source identity.
**Alternatives rejected:** varying wall colour is mostly perceptual and risks conflating role detection; varying “fill lowest versus highest” without separate authority would silently change labels.
**Probe/evidence:** `checks/parametric/priority-direction-seed17.json`, source hashes, public examples, and task tests.
**Failure mode/limit:** one seed and two settings are prototype evidence only; no production admission is claimed.

## D9: Lesson assembly and rotation policy

**Decision:** production lessons contain three ordered demonstrations and one query. For audit, require each of the four materialized pairs to serve once as query while preserving the remaining order.
**Rationale:** three examples are enough to show layouts and priorities while keeping lessons compact; rotations detect cases where only the original held-out position was identifiable.
**Alternatives rejected:** a production-only check could hide a weak demonstration; all pair permutations are costlier and were unnecessary after every cyclic held-out query passed.
**Probe/evidence:** `checks/lesson-census.summary.json`: 300/300 production lessons and 1,200/1,200 rotations, all source-bound.
**Failure mode/limit:** the census does not enumerate every possible schedule start or all demonstration permutations.
