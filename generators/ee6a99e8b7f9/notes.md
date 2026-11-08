# Working notes: ee6a99e8b7f9

Current generator SHA-256: `d099f8e48c144805cf9aa65b460bc572750005cc4c0e1edbf59481a9775a64f7`.
Canonical normalized rule hash: `faea8048f031` (unchanged in this review).
Imported associated notes retain their original evidence and timestamps in `evidence/associated_notes.jsonl`.

## Intended rule and domain

The grid uses literal background 8, filled gray (5) and pink (6) rectangular components, and exterior marker dots (9). Every dot is immediately outside exactly one rectangle edge and every rectangle owns at least one dot. Gray rectangles erase but their source dots remain and are copied to the nearest inner edge. Pink rectangles remain, their source dots clear, and their markers move to the rectangle's center row or center column while preserving the coordinate parallel to the approached edge. For an even approached pink axis the canonical Racket authority uses `floor((lo + hi) / 2)`, the lower-indexed center.

The accepted generator domain is intentionally bounded to 9–18 rows, 9–18 columns, one to seven shapes, colors `{5,6,8,9}`, separated same-color filled rectangles, and unambiguous exterior dots. Border-touching rectangles are lawful when their available markers remain unambiguous. Arbitrary colors, hollow/overlapping rectangles, ambiguous dots, larger grids, and more than seven shapes remain outside the declared domain.

## Current decisions

### D1 — Preserve authority; repair generation and validation

The Racket transformation is coherent and still matches all canonical labels, so this review did not alter the canonical program or `RULE_HASH`. The baseline failure was in selected-source behavior: malformed scalar call arguments were accepted, and accepted even-sized rectangles were absent from the scheduled teaching distribution. Rewriting the rule would have hidden those defects rather than repaired them.

### D2 — Use exact task colors and same-color connected rectangles

Background is literal 8 rather than the modal color. Shape components are same-color 4-connected filled rectangles. Dots are assigned geometrically to exactly one bounding-box edge. This preserves canonical behavior and avoids merging adjacent different-color objects in validation.

### D3 — Four deterministic production profiles

Accepted sample indices cycle through:

1. `9×9`, one canonical 3×3 pink rectangle;
2. `11×11`, three canonical 3×3 mixed-color rectangles;
3. `15×15`, five mixed rectangles led by a 4×4 pink witness plus additional non-3×3 geometry;
4. `13×13`, seven mixed rectangles including border contacts, thin shapes, and a 4×1 pink even-axis witness.

Every four consecutive accepted indices therefore contain two canonical anchors and two generalization profiles. A deterministic schedule was retained over purely random sampling because profile-floor support and semantic witnesses must be guaranteed at the lesson level.

### D4 — Reverse the earlier odd-only generalization choice

The prior v3.0 schedule generalized size but used odd dimensions only. That made `floor((lo+hi)/2)` observationally identical to the plausible `ceil((lo+hi)/2)` rival, even though `self_check` accepted even rectangles. Version 3.1.0 now permits dimensions 1–5 in general construction and authors even pink witnesses in profiles 3 and 4. The minimal source-bound counterexample is `counterexamples/review-5c22ad8e91c4bedd/case.json`; exact Racket evidence is beside it in `racket.json`.

### D5 — Preserve authored orientation for even-axis witnesses

A reflection across an even axis swaps the lower and upper center cells. Randomly rotating or reflecting an authored even witness can therefore relabel the intended tie direction. Profiles 3 and 4 keep their authored orientation; the odd-only canonical anchors and override-generated scenes retain the prior augmentation. This is a deliberate distribution restriction, not an implicit invariant. A future augmentation system would need to transform the hidden tie parameter together with the grid.

### D6 — Prevent source interactions from masking a witness

With multiple markers on one pink rectangle, a canonical target from one source can coincide with a rival target from another. The painter now prefers joint fixed-step/midpoint witnesses whose canonical and alternative destinations are pairwise disjoint before filling remaining markers. This makes the lesson evidence constructive rather than probabilistic.

### D7 — Strict public call scalars

`seed` must be a literal integer, `sample_index` a literal non-negative integer, and `difficulty` one of `None`, `easy`, `medium`, or `hard`. Booleans, floats, strings, negative indices, and unknown difficulty values fail before `gen_ctx`. Exact public overrides remain limited to `grid_h`, `grid_w`, and `n_shapes`; unknown keys and non-integers fail loudly.

### D8 — Separate accepted grammar from canonical strictness

`self_check` accepts the documented lawful domain. `strict_canonical_like` additionally requires one of the four canonical dimension/count profiles, 3×3 shapes, and the corresponding palette size. The measured strict rate is therefore meaningful without making lawful generalization invalid.

### D9 — Declare executable teaching rivals

Seven pure competitors are declared: fixed inward steps, upper midpoint on even pink axes, first dot only, pink-to-inner-edge, gray-to-centerline, keep pink source, and clear gray source. Both fixed steps and upper midpoint fit every unique canonical pair and are listed in `CANONICAL_SHORTCUTS`. Production lessons require four demonstrations; every five-pair tested window and every held-out query rotation refutes all declared competitors.

### D10 — Keep an independent oracle

`workspace/reference_probe.py` independently parses the geometry and compares the Python mirror with canonical pairs. Canonical Racket remains label authority. The independent implementation is a regression oracle, not a replacement for exact Racket execution.

### D11 — Proposed parametric extension remains separate

`workspace/parametric/` proposes one episode-level parameter, `pink_center_tie ∈ {lower, upper}`. `lower` is the exact canonical program; `upper` changes only the two midpoint expressions. Each retained episode uses three demonstrations and one query, every pair exposes an even pink axis, and labels are produced by executing the materialized Racket program. This is a proposed prototype only and is not wired into production generation, approval, or the canonical rule.

## Verification and remaining limits

The completed after battery is 12/12 green, task-local tests are 71/71 green, and the production lesson census materialized 300 lessons with 1,500 held-out query rotations, zero declared-rival ambiguities, zero errors, and 1,175 unique inputs. These are finite checks against seven declared rivals, not a proof that no undeclared hypothesis can fit a lesson. The full random support outside the deterministic four-profile schedule and semantic equivalence beyond exact grid hashes remain unproven.
## Current reviewer considerations

Source SHA-256: `d099f8e48c144805cf9aa65b460bc572750005cc4c0e1edbf59481a9775a64f7`.

# Decisions for `ee6a99e8b7f9` v3.1.0

## D1 — Preserve the canonical authority

**Choice.** Keep canonical Racket and `RULE_HASH="faea8048f031"` unchanged.

**Rationale.** Exact Racket execution, the independent geometry probe, and canonical-pair tests agreed. The failures were in call validation and lesson support, not in the transformation itself.

**Rejected alternative.** Changing the rule to avoid midpoint ties would hide an accepted-domain teaching defect and break source authority.

**Evidence / failure mode.** `checks/after/checks/ee6a99e8b7f9_after_authority_sync.json`; authority execution parity passed. A future authority change must be reviewed separately rather than smuggled through a generator repair.

## D2 — Treat background and task colors literally

**Choice.** Continue to use literal background 8, rectangle colors 5/6, and marker color 9; parse rectangles as same-color 4-connected filled components.

**Rationale.** Modal-background or mixed-color component heuristics can merge adjacent roles or reinterpret a sparse scene. The current contract is exact and matches the canonical rule.

**Rejected alternative.** Generic object extraction across colors was unnecessary and less auditable.

**Limits.** Same-color touching/overlapping rectangles remain outside the generated grammar.

## D3 — Keep a deterministic four-profile schedule

**Choice.** Cycle accepted indices through two canonical anchors and two generalization profiles:

1. 9×9, one canonical 3×3 pink rectangle;
2. 11×11, three canonical 3×3 mixed rectangles;
3. 15×15, five mixed rectangles led by a 4×4 pink witness plus non-3×3 geometry;
4. 13×13, seven mixed rectangles including border contacts, thin shapes, and a 4×1 pink even-axis witness.

**Rationale.** Every four-example lesson receives canonical grounding plus constructive generalization. Pure random sampling cannot guarantee either profile-floor support or rival separation.

**Alternative considered.** Resample until a lesson happens to contain all witnesses. Rejected because it is slower, harder to reproduce, and vulnerable to schedule drift.

**Evidence.** `checks/after/checks/ee6a99e8b7f9_after_profile_floor.json`; 60 exact/envelope hits in 60 draws, zero crashes.

## D4 — Reverse the prior odd-only size choice

**Prior choice.** Version 3.0 generalized sizes using only 1/3/5 dimensions.

**New choice.** Permit 1–5 dimensions in general construction and author even pink axes in both generalization profiles.

**Reason.** `self_check` accepted even rectangles, but all canonical/generated odd axes made lower and upper midpoint rules observationally identical. The exact counterexample in `counterexamples/review-5c22ad8e91c4bedd/case.json` proves the distinction.

**Rejected alternative.** Ban even rectangles in validation. That would narrow the documented lawful domain solely to avoid teaching it and would discard a useful reasoning boundary.

**Failure mode guarded.** Any future schedule that removes all even pink axes will make `pink_upper_midpoint` survive; the focused schedule/rival tests fail in that case.

## D5 — Preserve orientation for authored even-axis witnesses

**Choice.** Do not randomly rotate/reflect profiles 3 and 4; retain augmentation for odd canonical anchors and override-generated scenes.

**Rationale.** On an even axis, reflection swaps lower and upper center cells. Applying a geometric transform without also transforming the hidden tie convention can relabel the witness.

**Rejected alternative.** Continue unconditional augmentation. A red test showed it could invert the intended tie evidence.

**Future option.** A parameter-aware augmentation layer could transform both grid and tie setting together; that is beyond this task-local repair.

## D6 — Make multi-marker witnesses collision-safe

**Choice.** When fixed-step and midpoint ambiguities are both active, prioritize sources whose canonical and alternative destinations are pairwise disjoint before adding generic markers.

**Rationale.** With multiple exterior markers, a canonical destination from one source can coincide with a rival destination from another and erase the observable disagreement.

**Rejected alternative.** Merely increase marker count. More markers can make masking worse and does not guarantee separation.

**Evidence.** `test_all_declared_rivals_are_pure_and_each_five_pair_window_is_rotation_safe` and the 300-lesson census.

## D7 — Validate public call scalars strictly

**Choice.** Require literal integer `seed`, literal non-negative integer `sample_index`, and `difficulty ∈ {None,"easy","medium","hard"}`. Reject booleans, floats, strings, negative indices, and unknown difficulty values before schedule/context logic.

**Rationale.** The baseline `defect_lint` showed malformed scalars could be silently coerced or accepted, undermining deterministic replay.

**Rejected alternative.** Coerce with `int(...)`. This accepts booleans/floats/strings and makes source-bound replay ambiguous.

**Evidence.** Baseline failed `defect_lint`; final battery is 12/12 green. Focused invalid-call tests cover eleven malformed forms.

## D8 — Keep exact overrides small and constructive

**Choice.** Retain only `grid_h`, `grid_w`, and `n_shapes` as exact public overrides; unknown keys and non-integer/out-of-range values fail loudly.

**Rationale.** These controls can be honored jointly by construction. Advertising probabilistic or partially consumed controls creates false contracts, as the audit of `a286d31d63fb` demonstrates.

**Limit.** Overrides select scene constraints, not the hidden parametric-rule prototype.

## D9 — Separate accepted grammar from canonical strictness

**Choice.** `self_check` validates the full lawful grammar; `strict_canonical_like` measures the narrower canonical dimension/count/3×3 support.

**Rationale.** Conflating strict support with legal generation would either reject useful generalization or inflate canonical-support metrics.

**Evidence.** Semantic gate: 600 draws, 299 strict hits (`0.4983`) against floor `0.25`, zero generation errors.

## D10 — Require executable rivals and four demonstrations

**Choice.** Declare seven pure competitors: fixed inward steps, upper midpoint, first dot only, pink-to-inner-edge, gray-to-centerline, keep pink source, and clear gray source. Mark fixed steps and upper midpoint as canonical-fitting shortcuts. Use four ordered demonstrations plus one query, and require rotation evidence separately.

**Rationale.** Correct labels are insufficient when a plausible rival fits every demonstration and changes the query. Four profiles are the smallest deterministic schedule that carries both canonical anchors and both principal generalization witnesses without relying on random luck.

**Rejected alternative.** Three demonstrations sampled from the current cycle. Depending on start/holdout, this can omit one of the two canonical-fitting shortcut witnesses.

**Evidence.** `checks/after/checks/ee6a99e8b7f9_after_semantic_gate.json`; `checks/lesson-census-after.summary.json`.

**Limit.** Passing seven named rivals and bounded generic mutations is finite evidence, not universal induction.

## D11 — Keep the midpoint parameter as a proposed, isolated prototype

**Choice.** Implement `pink_center_tie={lower,upper}` under `workspace/parametric/`, selected once per episode. `lower` is exact canonical behavior; `upper` changes only midpoint tie selection. Each episode has three demonstrations and one query, and every pair contains an even-axis witness.

**Rationale.** This is a small semantic variant that preserves the family’s object roles and geometry while requiring the learner to infer an episode-level rule choice.

**Rejected alternatives.** Cosmetic recoloring, input-size-only parameters, and per-pair resampling do not change or consistently define the rule. Integrating the parameter into the production generator was also rejected because the current API is bound to a single canonical Racket program.

**Evidence.** `checks/parametric/pink-center-tie-v1/evidence.json`; lower/upper rule hashes `3d42a168...` and `8f0867c3...`. All eight retained pairs distinguish the alternate setting.

**Limit.** Two settings and two retained seeds are bounded prototype evidence. Shared production integration requires a separate API/approval decision.

## D12 — Retain failures and independent probes

**Choice.** Keep the failed baseline, exact-Racket counterexample, independent geometry oracle, audit probes, and interrupted `04e2...` override receipt.

**Rationale.** These artifacts let future agents distinguish repaired defects from hypotheses and avoid repeating source investigation.

**Evidence locations.** `checks/before/`, `repo/generators/ee6a99e8b7f9/workspace/reference_probe.py`, `checks/audit/`, and `counterexamples/review-5c22ad8e91c4bedd/`.
