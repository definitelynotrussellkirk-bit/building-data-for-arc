# Current notes: 926c6bd137d3

## Intended rule

Each lawful input has one to four disjoint hollow yellow rectangular frames. Every strict frame interior contains exactly one nonzero, non-yellow marker. Fill only zero interior cells with that frame's marker color; preserve the marker, yellow border, and every exterior cell.

## Current generator (v3.0.0)

- Pinned authority: `RULE_HASH = "575c55ee70e4"`.
- Truthful exact axes: `grid_h`/`grid_w` 10–18, `n_frames` 1–4, and `n_exterior_distractors` 1–4.
- Constructive four-slot placement guarantees the requested frame count; no retry/drop path remains.
- Every ordinary sample contains exterior colored distractors so preservation is observable.
- Four ordered teaching profiles use 1/2/3/4 frames and 1/2/2/3 marker colors; palette rotation covers all legal marker colors across blocks.
- Easy/medium/hard vary maximum frame side 4/5/6 without narrowing the public override domains.
- `_analyse` powers structural validation, override observation, the pure rule mirror, witnesses, and rivals.

## Reversed prior decisions

The prior v2.0.1 retry sampler silently under-produced four-frame requests, its validator accepted a marker moved outside the frame, and its ordinary distribution omitted exterior preservation evidence. The prior nine-axis metadata also included dead aliases/constants. Those choices were replaced by constructive placement, role-aware validation, mandatory exterior evidence, and four observable axes. The retained audit lead and reproductions are under `counterexamples/review-a7304ba015dd369f-v0001/`.

## Semantic contract

Four demonstrations are required. Named lesson competitors are: erase exterior cells, use one marker color globally, leave interiors blank, and fill every frame blue. None fits all canonical pairs, so `CANONICAL_SHORTCUTS` is intentionally empty. The schedule and 100-lessons-per-band census found no ambiguity against these declarations, including every query rotation.

## Known limits / open findings

The 2×2 slot layout is a coarse placement family, not the full space of non-overlapping rectangles. Census results cover declared rivals and sampled/fixed-seed schedules only; undeclared hypotheses and all seeds remain unproved. Training approval is external to this repair. No semantic Racket change was made; selected authority text was synchronized while archival raw code was preserved.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-a7304ba015dd369f:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ffd12ccb0525dd22e55d145a6915df0a122f87662fec78f109668aa019fa21b6`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Constructive sampler, mandatory exterior distractors, broader marker colors and per-frame role validation address three prior findings: omitted exterior teaching, dropped requested frames, outside-marker false acceptance. Reported52tests,1500rotation census and full battery. Explicit reviewer-reported disposition required. Exact repaired generator=22180fb5602050e2eaeb98949520b3f3bd11bd077bc056fcf35645931579fd39. Evidence=/home/user/Desktop/ARCpuzzles/var/review/new-return-tools-review/tool-disposition-proposals-nine.json sha256=76a7ea73fa5513ccc75ba5c5d6aad9abc549b59dfa65563ac320261676fd2870. Maintainer explicitly resolves this prior source-bound finding on accepted reviewer-reported repair; no independent rerun or universal correctness claim.

### Assessment or prior finding

## 926c6bd137d3

Generator SHA-256: `ffd12ccb0525dd22e55d145a6915df0a122f87662fec78f109668aa019fa21b6`.

### A2.1 — Reproduced support gap: exterior preservation is never taught

The rival “fill each frame correctly, then erase everything outside all frame boxes” matches **96/96** emitted grids in seeds **0–31**, indices **101+seed**, across all three bands. The correct Python control and Racket agree on all 96. But the erase-exterior rival disagrees with Racket and the recorded labels on **all five canonical pairs**, which contain exterior distractors that should stay untouched.

This rival is explicitly **not canonical-fitting**; the defect is the generator's omission of a canonical distinction. A canonical counterexample with actual Racket and rival outputs is retained in `checks/audits/926c6bd137d3.json`. It passes the current validator, is in the canonical task domain, and lies outside the emitted generator's support because the generator places no exterior distractors.

The same census observes marker colours only **1, 2, 3, 5**, consistent with the fixed placement-index palette in the source. Colours 6 and 8 occur in canonical markers but are not emitted by the current normal generator. This is an additional coverage observation, not a measured model failure.

### A2.2 — Reproduced defect: requested frames silently dropped

Requesting `n_frames=4` at hard difficulty for seeds **0–63**, indices **101+seed**, yields fewer than four frames in **16/64** draws. First retained witness: seed **5**, index **106**, **three** realised frames. The validator accepts it with the requested override metadata. The generated scene is otherwise within the documented task domain. Placement exhausts its retry loop and moves on without checking the requested total. The input and actual Racket output are retained as `frame_count_counterexample` in the same report.

### A2.3 — Reproduced validator defect: marker outside the frame accepted

Starting from seed **0**, index **101**, easy difficulty, move the sole marker from the interior to a cell outside the frame. The validator still returns no errors because it checks only that a yellow cell and another colour occur somewhere. Racket raises an error when it cannot find an interior marker. The mutated input and exact error are retained in the report.

This is **not** an emitted-domain or ordinary generation-crash claim: the mutation deliberately violates the documented per-frame-marker rule. It demonstrates a validator false acceptance.

Recommended repairs, not applied: add preserved exterior distractors, permute and repeat marker colours independently of placement order, check each connected frame's geometry and interior marker, and make requested placement counts exact or explicitly rejected. The canonical rule itself was not changed or accused of a normal-domain mismatch.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-a7304ba015dd369f-v0001/audit_assets.json), manifest SHA-256 `e4b9dd6145adee3117f676871512c621ede7f5be0001fde22cf06757e280adc1`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `22180fb5602050e2eaeb98949520b3f3bd11bd077bc056fcf35645931579fd39`.

# Decisions for 926c6bd137d3

## D1 — Make the public grammar truthful

**Prior choice:** v2.0.1 advertised nine axes (`palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, `texture`, and others), although several were aliases, constants, or unused. Its apparent rationale was broad combinatorial metadata rather than observable control; no stronger rationale was retained.

**New choice:** expose only `grid_h` (10–18), `grid_w` (10–18), `n_frames` (1–4), and `n_exterior_distractors` (1–4). Reject unknown keys and non-integer/bool scalar values.

**Alternatives rejected:** retaining compatibility aliases would keep unverifiable controls in the training interface; silently ignoring unknown keys would make misspelled experiments look successful.

**Evidence/failure mode:** the before override gate failed; the final override gate and all axis-corner tests pass. The remaining limitation is that axis observability proves the requested statistic, not semantic usefulness of every combination.

## D2 — Construct frame count instead of retrying

**Prior choice:** random free placement with 120 attempts per frame; a failed frame was silently skipped. The likely rationale was simple varied packing.

**New choice:** split each grid axis into two spans separated by one coordinate, form four disjoint slots, shuffle them, and place exactly the requested number of frames.

**Alternatives rejected:** increasing retry count only lowers, rather than removes, under-production probability; post-hoc fallback frames would bias placement and risk overlap.

**Probe:** prior audit `A2.2` found 16/64 hard `n_frames=4` shortfalls. Focused tests now assert exact count across every axis boundary and many seeds. The visible 2×2 slot family is a documented distribution restriction.

## D3 — Always teach preservation outside frames

**Prior choice:** ordinary generations contained only frames and their markers. This made “fill interiors, erase all exterior colors” observationally equivalent on 96/96 audited samples.

**New choice:** generate 1–4 non-yellow distractor cells strictly outside every frame box and leave them unchanged under the authority mirror.

**Alternatives rejected:** occasional exterior evidence could still leave complete lessons ambiguous; placing distractors merely outside interiors but on borders would corrupt frame roles.

**Probe:** `preserve_exterior` fires on 600/600 semantic samples; `erase_exterior` is refuted in every large-census lesson and rotation. Exterior distractors currently share one color per grid, which is sufficient for preservation but does not teach multi-color exterior noise.

## D4 — Use a four-profile marker curriculum

**Prior choice:** marker colors were `colors[i]`, so early frames were strongly tied to fixed numeric colors and many lessons had only one marker color.

**New choice:** schedule 1, 2, 3, and 4 frames with respectively 1, 2, 2, and 3 marker colors; rotate the starting palette across blocks so all eight legal colors appear. Three-frame lessons deliberately repeat one color to show that marker identity, not “all colors unique,” controls filling.

**Alternatives rejected:** forcing all markers distinct would introduce a shortcut; fully random colors could fail to expose multiple marker colors within a four-demo lesson.

**Evidence:** `multiple_marker_colors` fires 468/600 random semantic samples and every declared lesson refutes the global-single-color rival. `marker_not_blue` fires 589/600; each lesson refutes fixed-blue fill.

## D5 — De-correlate frame count and exterior count

**Prior intermediate choice:** both counts advanced through 1–4 in lockstep. The strict linter correctly identified a one-to-one proxy axis.

**New choice:** keep frame count tied to the four teaching profiles, but advance exterior count by seed, block, and a residue multiplier so each frame count co-occurs with all exterior counts over blocks.

**Alternative rejected:** randomizing exterior count independently per draw would be acceptable for diversity but less reproducible for exact schedule analysis.

**Probe:** `test_default_frame_and_exterior_axes_are_not_one_to_one_locked` failed before the change and passes now. This removes deterministic identity, not every finite-sample correlation.

## D6 — Make difficulty real but non-blocking

**Prior/intermediate choice:** difficulty was accepted but did not change any draw; defect lint flagged it as dead.

**New choice:** easy/medium/hard cap frame sides at 4/5/6 and use a difficulty-bound placement stream. Public exact axes remain legal in every band.

**Alternatives rejected:** restricting grid or count overrides by band would contradict declared global domains; changing semantic roles by difficulty would fragment the task.

**Probe:** a focused regression holds public axes fixed and observes geometry changes across bands. Difficulty controls geometry only, so some individual seeds may coincidentally share dimensions or layouts.

## D7 — Separate authority validity from generated envelope

**Prior choice:** `self_check` required only one yellow and one non-yellow cell anywhere; degenerate textures bypassed it.

**New choice:** `self_check` accepts the complete lawful authority grammar, including all five canonical inputs. `generation_check` separately requires ordinary dimensions/counts and exterior evidence.

**Alternatives rejected:** baking ordinary distribution requirements into `self_check` would reject canonical inputs; keeping degenerate bypasses would let malformed training grids appear valid.

**Probe:** tests mutate markers, borders, frame count, overlap, cell types, and dimensions. The generic battery rejects 48/53 destructive mutations; the five “absent color” survivors are not necessarily illegal for this task because marker colors are intentionally variable.

## D8 — Four demonstrations and explicit rivals

**Prior choice:** no semantic contract or declared teaching minimum.

**New choice:** `EXAMPLES_NEEDED=4`, four schedule profiles, four witnesses, four lesson competitors, and `lesson_identifiable`. `CANONICAL_SHORTCUTS` is empty because none of these rivals fits every canonical pair.

**Alternatives rejected:** two or three unconstrained examples can omit multi-color or exterior evidence; misclassifying partial rivals as canonical shortcuts would fail the canonical-fit contract (as reproduced in audit target `e9905db3a38d`).

**Evidence:** 12/12 fixed-seed schedule lessons and 300/300 broader lessons pass; all 60 and 1,500 respective rotations pass. This is finite declared-rival evidence, not formal rule uniqueness.

## D9 — Synchronize authority text without changing the rule

**Prior choice:** selected `racket_target.target_code` was textually out of sync and the generator lacked `RULE_HASH`.

**New choice:** pin `575c55ee70e4` and apply the official authority-sync proposal. Only selected `target_code` changed; archival `raw_code` remains unchanged.

**Alternative rejected:** editing canonical rule semantics was unnecessary because the existing Racket behavior already matched all five labels and the pure Python mirror.

**Evidence:** final rule smoke, Racket lint, authority sync, and all canonical exactness tests pass; execution parity is PASS.

## D10 — Preserve failed iterations as evidence

The first after run exposed a one-to-one count proxy; an isolated defect-lint run then exposed dead difficulty; the second complete battery exposed a missing exhaustive schedule receipt. These were not deleted or relabeled as passes. The final run uses the unchanged final generator plus `checks/schedule-census.json` and is the only aggregate claimed green.


## Compatible canonical marker palette control (3.0.1)

This revision ports one bounded improvement from the separate review-134d82626bc7bd77 proposal onto the current accepted four-demonstration generator. The alternate three-demonstration candidate is not adopted. Existing dimensions, frame and exterior-distractor axes, all four prior rivals, placement, and complete lesson validation are preserved.

A `canonical_marker_palette` rival fills only frames whose marker color appeared in the five canonical pairs. That shortcut fits all five canonical pairs. Scheduled samples at residues 2 and 3 use a noncanonical marker color when the planned palette would otherwise contain only canonical colors. Each five-sample consecutive window therefore has at least two such controls, leaving one in four demonstrations after any query holdout. The new rival and lawful novel-marker witness join the existing semantic hooks.

Qualification is finite and task-local: the original indices 3 through 7 regression failed before the change; the staged 3.0.1 candidate passed all 52 existing task cases and four new cases. Actual public Racket authority labelled the 20 seed-0 inputs at indices 3 through 7 across default/easy/medium/hard plus five canonical inputs, and matched the candidate mirror on all 25. This is not a full census or training admission. The maintainer receipt binds these checks to the exact source hash.
