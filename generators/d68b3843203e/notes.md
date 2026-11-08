# Review notes — 2026-09-28

Proposal v1.3.0 builds on accepted v1.2.2. The prior source was structurally strong but used uniform defaults for two task-level axes despite canonical 80/20 marginals. The final source weights frame count 2/3 as 20/80 and cue size 1/2 as 80/20, independently. Frozen-baseline 480-call counts were frames 212/268 and cues 272/208; final counts are 76/404 and 376/104. All four joint combinations remain live.

Count coverage is now 75%. The first after attempt retained at `checks/after-attempt1` failed strict transformation drift because color 8 was newly added on exactly 30/60 samples. An 80% experiment fixed that detector but reduced repeated-count support to 7/120; 75% passes both. Final census has 46 repeated-count scenes, 274 touching count-2 witnesses, 35 separated count-3 witnesses, and 293/480 topology-rival disagreements.

The selected canonical and base target Racket sources replace `(let ((dummy 0)) ...)` with `(let () ...)`, removing the only Racket-linter finding. Behavior was checked before editing on all canonical pairs plus 50 generated cases, then by final rule smoke, authority parity, and reviewer replay. Selected RULE_HASH is `90de3c06fb83`. Archival `raw_code` stays unchanged and execution-equivalent.

Final verification: 12/12 after stages green; 61 focused tests; 600/600 strict semantic census; 18,900 override draws; 300 diversity pairs with 100% unique inputs/outputs; 245 exact reviewer Racket comparisons; 40 D4 checks; zero final Racket-lint findings. The five-example marginals are a prior, not a hidden-distribution claim, and difficulty remains uncalibrated.

Reviewer tooling now reports canonical/generated frame/cue profiles, handles singleton canonical test dictionaries, and replays the current audit assignment. The audit found concrete canonical-fitting shortcuts in 4a3ababcaceb and cf60523d1603; target sources were not modified.
## Current reviewer considerations

Source SHA-256: `ffb8ab55d42c9eb82125de4c3a316465a64eb0123d7b065d41bf05f2b01a82f5`.

# Decisions: d68b3843203e

## 1. Selected Racket source

**Original rationale:** unknown; the rule used a dummy binding, `(let ((dummy 0)) ...)`, apparently only to create an internal-definition scope.
**Decision:** replace it with the semantically equivalent empty binding form, `(let () ...)`, in canonical `program_solution` and selected base `target_code`; preserve archival `raw_code`.
**Alternatives considered:** leave the linter finding; rewrite the whole rule; alter only one authority.
**Probe:** actual protected Racket old/new parity on all five canonical pairs plus 50 generated inputs before editing; final rule smoke, Racket lint, authority sync, and 245 reviewer-probe comparisons.
**Failure modes:** source mismatch, changed internal-definition scoping, or an archival source being mistaken for selected authority.
**Limitations:** the archival spelling remains different, although execution parity is verified.

## 2. Number of frames

**Original rationale:** prior source used a uniform `draw_int(2, 3)`; no rationale was retained.
**Decision:** default weights 2/3 as 20/80 while retaining exact override support for both values.
**Alternatives considered:** retain 50/50; force three frames; replay the five canonical profiles as a finite schedule.
**Probe:** canonical 1/5 vs 4/5; frozen baseline 212/480 vs 268/480; final 76/480 vs 404/480; override battery 18,900 draws.
**Failure modes:** overfitting a five-example marginal or starving two-frame examples.
**Limitations:** this is a prior, not a claim about hidden evaluation frequency.

## 3. Cue size

**Original rationale:** prior source used uniform `draw_int(1, 2)`; no retained rationale.
**Decision:** default weights 1/2 as 80/20, with both override values preserved.
**Alternatives considered:** retain 50/50; force one cell; copy the canonical frame/cue joint schedule.
**Probe:** canonical 4/5 vs 1/5; frozen baseline 272/480 vs 208/480; final 376/480 vs 104/480.
**Failure modes:** treating a nuisance cue as more predictive than it is.
**Limitations:** cue shape remains a point or straight domino only.

## 4. Joint frame/cue profile

**Original rationale:** both axes were independently uniform.
**Decision:** preserve independence after marginal weighting. The final 480-call joint census contains 52 `(2,1)`, 24 `(2,2)`, 324 `(3,1)`, and 80 `(3,2)`.
**Alternatives considered:** emit only the two canonical combinations; create a linked profile axis.
**Probe:** all four combinations appear in regression tests and reviewer census.
**Failure modes:** copying the canonical perfect correlation would make cue size a shortcut for frame count.
**Limitations:** independent weighting intentionally produces valid combinations absent from the five examples.

## 5. Marker-count coverage schedule

**Original rationale:** two thirds of lessons forced broad count coverage; one third sampled counts independently.
**Decision:** use three quarters coverage and one quarter independent counts.
**Alternatives considered:** retain two thirds; use four fifths; force coverage in every lesson; remove cue color 8.
**Probes and iteration:** the first final-source attempt introduced color 8 in exactly 30/60 strict-defect samples because count-3 frames and cue-color overlap combined badly. Four-fifths coverage cleared that issue but yielded only 7 repeated-count lessons in a 120-call regression, below the retained floor of 8. Three-quarters cleared strict defect lint and preserved the repeated-count floor. Final 480-call census has 46 repeated-count scenes, 274 touching-pair witnesses, and 35 separated-three witnesses.
**Failure modes:** forced 1/2/3 counts can make every frame count unique and teach an ordering shortcut; too little coverage can omit output color 8.
**Limitations:** coverage is deliberately biased and is not intended to be frequency-calibrated.

## 6. Grid height and width

**Original rationale:** canonical-scale dimensions were weighted while retaining broader 8..16 by 8..18 support.
**Decision:** unchanged.
**Alternatives considered:** narrow to exact canonical dimensions; broaden to full ARC 1..30.
**Probe:** final profile floor has exact hits in every band and 35/60 envelope hits; override battery spans the declared domains.
**Failure modes:** narrow dimensions invite template memorization; very large dimensions dilute the transformation.
**Limitations:** the weighting is handcrafted.

## 7. Frame geometry and placement

**Original rationale:** separated constructive slots guarantee feasible 2/3-frame layouts, including 8x8 boundaries, while varying aspect ratio and edge contact.
**Decision:** unchanged.
**Alternatives considered:** rejection sampling; fixed 4x4 frames; copying canonical boxes.
**Probe:** final census has 20 frame shapes, 328/480 calls with an edge frame, 288/480 with a thin frame, and no self-check failures.
**Failure modes:** attached yellow cells, overlapping/nested frames, or infeasible count-3 interiors.
**Limitations:** frames are axis-aligned rectangles only, matching the selected rule's intended domain.

## 8. Marker topology

**Original rationale:** positions are independently sampled inside each frame so connectivity does not encode count.
**Decision:** unchanged and retained as a first-class semantic challenge.
**Alternatives considered:** fixed motifs for each count; always separated markers; always connected markers.
**Probe:** canonical topology rival fits 5/5 public pairs, while final semantic gate verifies 60 touching-pair and 51 separated-three counterexamples.
**Failure modes:** count 2 always separated and count 3 always connected would let topology replace counting.
**Limitations:** marker counts remain limited to 1..3 because the selected rule maps them to ARC colors 6..8.

## 9. Cue color and position

**Original rationale:** one irrelevant exterior cue of color 5..9 is preserved by the rule and can touch an outer edge.
**Decision:** leave color and placement support unchanged, including color 8.
**Alternatives considered:** remove cue color 8 to satisfy the transformation-fingerprint heuristic; constrain cues to the canonical colors 5/6/7/9.
**Probe:** the strict-defect failure was fixed by improving count coverage rather than deleting a useful nuisance overlap. All final gates pass.
**Failure modes:** placing a cue inside a frame, overlapping a border, or making cue color predictive of output.
**Limitations:** only one cue object is emitted.

## 10. Difficulty bands

**Original rationale:** easy/medium/hard cap maximum frame side at 5/6/7.
**Decision:** unchanged.
**Alternatives considered:** vary counts, number of frames, or cue complexity by band.
**Probe:** all bands pass semantic, profile, override, and self-check gates.
**Failure modes:** changing semantic support by band would produce dead witnesses.
**Limitations:** difficulty has not been calibrated against human or model solve rates.

## 11. Validation and override contract

**Original rationale:** component-exact yellow-frame parsing, strict red-marker placement, and observable exact axes were added in the prior accepted review.
**Decision:** preserve the implementation and add regressions around newly weighted defaults.
**Alternatives considered:** loosen `self_check` to any rectangular outlines; add linked-profile overrides.
**Probe:** mutation-sensitive self-check stage green; 18,900 override draws green; unknown keys and invalid types rejected.
**Failure modes:** a closed border with an attached yellow spur, outside red marker, malformed cell, or unobserved override.
**Limitations:** `strict_canonical_like` intentionally checks the structural domain, not empirical frequencies.

## 12. Reviewer tooling

**Original rationale:** the prior workspace had independent frame enumeration and Racket replay, but no frame/cue profile report; its audit probe referenced an older packet's IDs.
**Decision:** add `scene_profile`, canonical/generated marginal and joint histograms, singleton test-pair normalization, and current executable audit rivals.
**Alternatives considered:** record findings only in prose.
**Probe:** 16 reviewer-tool tests pass; current audit probe verifies every canonical pair and 40 ordinary protected-Racket draws per target.
**Failure modes:** stale audit IDs, assuming `test` is always a list, or relying on a Python mirror as label authority.
**Limitations:** the tools require this repository and supplied Racket runtime.
