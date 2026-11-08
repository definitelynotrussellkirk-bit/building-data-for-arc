# Current account: b7fbb716d189

## Intended rule

Find the unique corner token (`1..4`) and the connected interior motif (colors `5..9`). Crop the motif to its nonzero bounding box, preserving internal zeroes, then apply the transform selected by token value: `1` identity, `2` clockwise rotation, `3` 180-degree rotation, `4` transpose. Selected rule hash: `5ac5138de6ce`.

## Reversed baseline decision

Prior choice: the baseline fixed the token at top-left and exposed texture/degenerate controls that did not represent the authoritative domain. The original rationale is unknown. That choice let a canonical-fit shortcut infer the transform from token corner and caused canonical, override, validator, profile, semantic-contract, and authority-sync problems.

New choice: token value and all four corners vary independently. The default deterministic offset schedule retains canonical associations at offset zero and creates explicit noncanonical pairings at offsets one through three; exact corner overrides support the full cross-product. Evidence: `counterexamples/review-73698e4c67667471-shortcut/` and `workspace/reference_probe.py`.

## Contract and decisions

- Version `3.0.0`; exact axes are height `8..12`, width `8..13`, token `1..4`, four corners, motif cells `5..9`, and motif colors `2..5`.
- Unknown, mistyped, and out-of-range overrides are rejected; `observe_overrides` round-trips every valid control.
- Inputs require one corner token, zero elsewhere on the border, and one 4-connected interior motif no larger than `4x4` whose four transform outputs are distinct.
- Canonical-profile dimensions/palette support is present in every band; all exact controls remain available in every band.
- `corner_encodes_transform` is the declared semantic rival/canonical shortcut/lesson competitor. Three-demo lessons must refute it.
- The selected base Racket source was synchronized to the unchanged canonical rule; there was no semantic Racket change.

## Final evidence

Final generator SHA-256: `cb00268a1946d02e3612f23e3651f222ac533662dc912565052bdd040f32e5ac`.

- Battery: 12/12 green (`checks/after/checks/b7fbb716d189_after_battery_summary.json`).
- Focused regressions: 48/48 passing (`checks/task-tests-final.json`).
- Independent sampling: 768 inputs, all 16 token/corner pairings per band, zero self-check failures/nondeterminism, 576 shortcut disagreements (`checks/independent-probe.json`).
- Lessons: 300 production lessons and 1,200 query rotations, zero declared-rival ambiguities (`checks/lesson-census.json`).
- Post-repair visible solve: one revision, 3/3 demonstrations passed, earlier exposure declared yes and no reference consulted during solve (`solve/summary.json`).

## Known limits and open findings

These are finite checks against declared rivals, not a proof of universal identifiability. Tokens and motif colors occupy distinct canonical role ranges by rule. Catalog approval/training-safety status is unchanged and remains outside this repair. There is no known selected-task blocker; audit-only findings for other generators are in `AUDIT.md`.
## Current reviewer considerations

Source SHA-256: `cb00268a1946d02e3612f23e3651f222ac533662dc912565052bdd040f32e5ac`.

# Decisions: b7fbb716d189

## D1 — Treat token value, not token location, as causal

The selected Racket rule maps token values `1..4` to identity, clockwise rotation, 180-degree rotation, and transpose. The baseline generator instead fixed the token at top-left; its original rationale is unknown. The five canonical pairs also happen to pair each corner with one operation, so the strongest plausible rival can ignore token value and infer the operation from position.

Decision: preserve the authoritative token-value mapping and make corner an independent nuisance variable. Rejected alternatives were (a) retaining top-left only, which leaves the shortcut perfect, and (b) treating the canonical corner association as part of the rule, which contradicts the selected Racket program. Evidence: `checks/shortcut-counterexample/` and `workspace/reference_probe.py`.

## D2 — Use a deterministic corner-offset schedule

For default generation, token value is drawn normally and the corner is the canonical corner shifted by `sample_index mod 4`. Offset zero keeps canonical-profile examples; offsets one through three break the corner mapping. Any three consecutive pair indices include a disagreement, matching the production lesson policy of three demonstrations.

A purely random corner draw was rejected because a finite lesson could accidentally preserve the shortcut. Forcing every sample to a noncanonical corner was also rejected because canonical support matters for distribution fidelity. Exact `token_corner` overrides bypass the schedule and support all four values in every band.

Failure mode: a consumer that reorders or samples demonstrations by a different policy could weaken the deterministic guarantee. This is why the final census checks both actual production assembly and every query holdout of each four-pair bundle.

## D3 — Keep six exact, observable controls only

The repaired `AXES` are `grid_h`, `grid_w`, `token`, `token_corner`, `motif_cells`, and `motif_colors`. Every advertised value is constructively supported in all difficulty bands, `observe_overrides` recovers each value from the grid, and unknown or malformed controls fail immediately.

The baseline texture/degenerate controls were removed rather than preserved as aliases because they were dead or overlapped unrelated semantics. Broadening the contract with position, palette, or texture controls was rejected as unnecessary for the rule and harder to validate exactly. The final override stage and focused cross-product tests cover this choice.

## D4 — Require a connected, transform-distinguishing motif

The motif uses `5..9` interior cells, `2..5` colors from `5..9`, a bounding box no larger than `4x4`, and 4-connectivity. Generation resamples until identity, clockwise, 180-degree, and transpose outputs are all distinct.

Allowing symmetric crops was rejected because they can erase the causal effect of one or more token values and create additional lesson ambiguity. Requiring a solid rectangle was also rejected because it would introduce a stronger shape shortcut and reduce canonical fidelity. Destructive-mutation tests cover missing/duplicate tokens, disconnected motifs, border leakage, and blanks.

## D5 — Preserve canonical profiles without narrowing the domain

Every band heavily samples canonical-like `8..10` dimensions and three motif colors, with a smaller broad-profile branch that follows band-specific biases. Exact overrides remain authoritative over both branches. This was chosen over band-disjoint hard ranges because the profile-floor gate expects canonical support in every band and because difficulty should not redefine task semantics.

Measured support is retained in `checks/independent-probe.json` and the final battery. The finite probe is distribution evidence, not proof that every random seed is unique.

## D6 — Declare and test the actual canonical-fit rival

`corner_encodes_transform` is registered in all three semantic interfaces, and the lesson hook rejects any lesson whose demonstrations fail to refute it. The independent probe first verifies that this rival fits all five canonical pairs before using it as a diagnostic.

A generic list of speculative rivals was rejected: only an executable, source-bound rival with an exact disagreement is used. This does not prove uniqueness among all programs; that limitation is explicit in the census report and review.

## D7 — Production lesson and query-rotation policy

Production materialization uses exactly three demonstrations and one query from consecutive accepted pair indices. The final census requests 100 lessons in each of easy, medium, and hard, with deterministic SHA-derived seeds and consecutive starts. The required rotation policy reuses each labelled four-pair bundle, holds out every pair once as query, and preserves the relative order of the other three.

Results: 300/300 production lessons, 1,200 labelled pairs, and 1,200 unique input hashes; zero production ambiguities. The 1,200 query rotations also have zero ambiguities, hook warnings, or scoring errors. I did not claim enumeration of every cyclic window or any undeclared rival.

## D8 — Synchronize the selected authority copy without changing semantics

The selected base solution JSON and canonical catalog row had equivalent normalized Racket but different exact text. The selected base copy was synchronized to the canonical rule text. The rule hash remains `5ac5138de6ce`; canonical `puzzles.jsonl` was not edited; final authority sync and execution parity pass.

Changing the Racket algorithm was rejected because the repair target was the generator/curriculum, not the authoritative transformation.

## D9 — Retain exact counterexamples and reusable tooling

The bottom-left/token-2 example is retained under `repo/generators/b7fbb716d189/counterexamples/review-73698e4c67667471-shortcut/` with input, rival output, supported Racket receipt, and source-bound probe metadata. A focused test loads those files directly. `workspace/reference_probe.py` is intentionally task-local tooling that future agents can rerun against source or staged generator bytes.

The before battery and initial failing test evidence were retained rather than overwritten. Large runtime copies and duplicate repositories are excluded from the return.

## Known limitations and open findings

- The claims are finite and rival-bounded; they do not prove universal program identifiability.
- Catalog approval remains false and training safety remains unsafe/unapproved; this review does not alter those statuses.
- The post-repair visible solve only needed demonstrated token values `2` and `4`; it deliberately did not guess unseen token meanings `1` and `3`, although the generator and Racket authority test all four.
- No selected-task blocker remains. Separate audit-only findings are documented in `AUDIT.md` and were not repaired here.
