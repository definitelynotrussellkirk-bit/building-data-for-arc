# Working notes: fb7f02aa9ab0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `cd80f7ce93c747ba54eb1a2818599e6a502d082187fc5b728a3c34d7419550f7`.

# Decisions for fb7f02aa9ab0

## Scope and evidence basis

The repair changes the selected generator, its task-local tests, its stale `SUMMARY.md`, and one task-specific archived Racket `target_code` copy whose only difference from canonical was two comments. The canonical row and canonical Racket behavior were not changed. No prior return was available as a substantive lead: `evidence/associated_notes.jsonl` was empty, so the frozen baseline, canonical examples, and the required before battery were the evidence basis.

The before battery was interrupted after checkpointing several stages, but it had already established the decisive defects: lint reported a missing `RULE_HASH` and four warnings; `self_check` rejected 3 of 5 canonical inputs; defect lint found four dead textures, domain overlap, and exact-source divergence. Those artifacts remain under `checks/before/`.

## D1 — Keep the canonical transformation unchanged

**Choice.** Preserve control mapping 3=union, 4=intersection, 6=symmetric difference; normalize colors 1 and 2 independently; crop and paint the result with 8. Pin `RULE_HASH = "27a3cc4c9462"`.

**Rationale.** The canonical authority passed rule smoke before the repair and all five canonical pairs are internally consistent. The defects were in sampling, validation, source synchronization, and lesson teaching—not the transformation.

**Rejected alternatives.** I rejected altering operation colors, output color, cropping, or normalization semantics. I also rejected treating the archived comment-only source difference as a new authority.

**Probe.** The Python semantic mirror matches 5/5 canonical outputs, rule smoke passes, authority sync passes, and the post-repair solve inferred the same rule from visible examples.

**Limit.** A Python mirror is an executable cross-check, not a replacement authority; Racket remains canonical.

## D2 — Dimensions: 8–20 rows and 11–24 columns, canonical-weighted in every band

**Choice.** Advertise exact `grid_h` 8..20 and `grid_w` 11..24. Unoverridden draws use an 11:1 core/broad profile. Easy, medium, and hard core anchors are respectively 8×11, 9×12, and 10×13; broad draws retain the full legal range with band-favored weights. Exact overrides are legal in every band.

**Rationale.** Canonical inputs occupy 8–10 rows and 11–13 columns, while broader canvases improve placement and visual diversity. The prior band logic disappeared from the actual draw path, so easy/medium/hard produced byte-identical instances for every sampled seed.

**Rejected alternatives.** I rejected disjoint per-band ranges because they make valid exact overrides band-dependent and can remove canonical support from hard. I rejected one uniform range because it leaves difficulty observably dead. I rejected the baseline's larger minimums because they excluded canonical 8×11 and 9×12 profiles.

**Probes.** Profile floor: 58/60 exact canonical-profile hits across seeds 0–19 per band, with at least 19/20 in each band. Task tests verify distinct band outputs. Override contract accepted all declared dimensions in all bands.

**Failure modes/limits.** Difficulty is a sampling curriculum, not a formal complexity metric. The 11:1 weighting intentionally concentrates training near canonical scale; very large canvases are less frequent.

## D3 — Control colors: deterministic 3/4/6 coverage in every three-example lesson

**Choice.** Schedule `control_color` cyclically over `(3,4,6)` with a stable seed-dependent phase. Exact overrides still use the normal draw API.

**Rationale.** A three-example lesson must expose the entire legend. Independent random draws can repeat one operation, allowing a fixed-operation rival to fit all demonstrations.

**Rejected alternatives.** I rejected pure random sampling and post-hoc resampling because neither makes lesson coverage source-obvious or exactly replayable. I rejected deriving the control from difficulty because that entangles unrelated axes.

**Probes.** All 3,600 cyclic windows (3 bands × 100 seeds × 12 starts) contain all three controls. The 300-lesson census refuted each fixed-operation rival in every lesson.

**Failure modes/limits.** The period is predictable. This is deliberate curriculum structure; stable seed-dependent phase prevents every seed from starting with the same operation.

## D4 — Control position: all four corners

**Choice.** Schedule `top_left`, `top_right`, `bottom_left`, and `bottom_right` across four consecutive samples.

**Rationale.** Canonical inputs use multiple corners, while the baseline hard-coded top-right and its validator rejected bottom-right and top-left canonical inputs. Position is a nuisance variable and should not become part of the learned rule.

**Rejected alternatives.** I rejected unrestricted interior controls because canonical evidence supports corner legends and interior cells can collide visually with shapes. I rejected random corners because complete local coverage is cheap.

**Probes.** Exact override tests recover every position; 3,600 cyclic four-example windows cover all four corners; all five canonical inputs pass `self_check`.

**Failure modes/limits.** Non-corner legends remain outside the strict teaching manifold.

## D5 — Normalized relation: partial overlap plus both strict subset directions

**Choice.** Generate `partial`, `a_subset_b`, and `b_subset_a`, scheduled once each in every three-example lesson. Masks must overlap and be unequal.

**Rationale.** Canonical data includes a subset case. The baseline demanded a private cell for both masks, rejected that canonical input, and restricted the Boolean algebra to partial-overlap geometry. Both subset directions prevent color-role-specific shortcuts.

**Rejected alternatives.** I rejected disjoint masks because intersection would be an empty 1×1 output and fixed union/XOR become observationally identical. I rejected identical masks because XOR would be empty and several operations collapse. I rejected only one subset direction because it couples role/size to color.

**Probes.** Exact relation overrides are recovered by `observe_overrides`; the strict semantic gate accepted 600/600 generated instances and 5/5 canonical inputs; all 3,600 cyclic lesson windows cover all three relation types.

**Failure modes/limits.** The sampler intentionally excludes disjoint and identical masks to keep all three operation demonstrations informative. It is a teaching distribution, not the full mathematical input domain of the Racket function.

## D6 — Origin support: include and omit normalized coordinate `(0,0)`

**Choice.** Schedule `origin_kind="corner"` and `"split"`. In corner mode both masks include `(0,0)`. In split mode both touch normalized row 0 and column 0 but omit `(0,0)`, using the connected seed `{(0,1),(1,1),(1,0)}`.

**Rationale.** Independent top-left normalization does not imply the top-left bounding-box cell is occupied. The baseline forced both masks through `(0,0)`, allowing a corner-anchor shortcut.

**Rejected alternatives.** I rejected mixed modes where only one mask contains `(0,0)` for this repair because two clear modes are easier to observe and validate. I rejected arbitrary disconnected top/left support because canonical shapes are object-like and 4-connectedness is useful.

**Probes.** Exact overrides are observable; every three-example cyclic window contains both modes; the independent-normalization witness fires on 600/600 semantic-gate samples and refutes the absolute-coordinate rival.

**Failure modes/limits.** Mixed origin occupancy is outside this version's advertised domain. Future expansion should add an explicit mode rather than silently broadening `split`.

## D7 — Shape morphology: 4-connected growth inside a bounded normalized box

**Choice.** Build both masks by connected growth in a 3–6-ish normalized box, sharing a connected core and adding relation-specific cells. Place them as separated physical objects with a one-cell clearance from existing foreground.

**Rationale.** This guarantees one object per color, lets relation types be constructed rather than hoped for, and separates physical placement from normalized semantics. It removes the baseline fallback that could return a partially placed grid after repeated failure.

**Rejected alternatives.** I rejected independent Bernoulli cells because they commonly fragment into multiple components and make relation guarantees expensive. I rejected a fixed shape library because it creates duplicates and morphology shortcuts. I rejected silently returning the last failed grid; generation now raises on impossible placement.

**Probes.** `self_check` is clean on 60/60 defaults and rejects 60/60 destructive mutations; lint observed 100% unique inputs in the larger diversity check; generation produced 1,200 unique inputs in the lesson census.

**Failure modes/limits.** The bounded growth model does not cover every connected polyomino or large thin structure. It favors compact shapes and caps private growth increments at four cells.

## D8 — Exact override contract and observability

**Choice.** Reject unknown override keys. Keep only six real axes. Implement `observe_overrides` for every exact axis and declare no incompatible combinations.

**Rationale.** Baseline metadata included singleton/dead/fake axes and accepted unknown keys through `**overrides`. Without observation, a generator can clamp or ignore requested values while appearing to succeed.

**Rejected alternatives.** I rejected retaining old diagnostic aliases (`texture`, `palette_kind`, fixed palette-size axes) because they did not represent independent generated behavior. I rejected a legacy compatibility policy because this task can honor every Cartesian combination exactly.

**Probes.** Exhaustive override contract: 54,090/54,090 draws accepted, 601 override cases, three bands, zero combination rejections. Four targeted structural combinations are also asserted in task tests.

**Failure modes/limits.** The exhaustive matrix is expensive and produces a large artifact. That is a tooling issue recorded as F1, not a reason to weaken exactness.

## D9 — Validator and strict profile

**Choice.** `self_check` validates rectangularity, allowed colors, one control, both connected shapes, overlapping unequal normalized masks. It deliberately accepts all legal control corners and subset cases. `strict_canonical_like` additionally enforces corner placement and generated dimension bounds.

**Rationale.** A validator should check the transformation's lawful domain, not re-impose one sampler shortcut. The baseline validator encoded top-right and two-private-cells assumptions and rejected 3/5 canonical inputs.

**Rejected alternatives.** I rejected requiring `(0,0)` occupancy or partial overlap. I rejected a validator that only checks color counts, because disconnected shapes can alter normalization semantics.

**Probes.** All 5 canonical inputs accepted; 600/600 generated strict; 60/60 destructive mutations rejected; task tests cover all canonical inputs.

**Failure modes/limits.** `self_check` does not require the control to be at a corner, because the Racket rule is color-based and a lawful hand-built input can place it elsewhere. The strict hook carries the sampler-specific corner constraint.

## D10 — Executable semantic oracle, witnesses, and rivals

**Choice.** Add a Python mirror, four rivals (`union_only`, `intersection_only`, `xor_only`, `absolute_coordinates`), four witness predicates, and expose the rivals through all required contract names.

**Rationale.** Syntax, diversity, and profile gates cannot show that a generator teaches the legend or independent normalization. Executable rivals make those claims falsifiable.

**Rejected alternatives.** I rejected prose-only claims and string labels without callables. I rejected a very large rival set because finite plausible rivals are useful while arbitrary program enumeration is not.

**Probes.** Semantic gate verified 4/4 witnesses and 4/4 rival claims over 600 samples; task tests verify canonical oracle agreement and direct rival disagreement; lesson census refuted all four logical rivals in 300/300 lessons.

**Failure modes/limits.** Passing declared rivals is not universal identifiability. Undeclared shortcuts may remain; this is stated in the review brief.

## D11 — Archived authority source synchronization

**Choice.** Remove two explanatory comments from the task-specific archived `target_code` so it is byte-for-byte the canonical Racket program. Leave `raw_code`, canonical data, rule hash, and behavior unchanged.

**Rationale.** Exact-source authority sync is an after-phase requirement. The differing archive was semantically equivalent but produced a persistent `rule-source-divergence` warning.

**Rejected alternatives.** I rejected editing canonical source to match the beautified archive and rejected suppressing the warning. Canonical is the authority.

**Probes.** Defect lint moved from one remaining warning to zero; authority sync and rule smoke pass; canonical rule hash remains `27a3cc4c9462`.

**Failure modes/limits.** This is a textual synchronization, not a semantic rule repair.

## D12 — Self-review for newly introduced shortcuts

The repair could have introduced periodic schedules or compact-growth signatures. I checked every start in the 12-sample combined schedule for 100 seeds per band: all 3,600 three-demo windows cover operations, relations, and both origin modes, while their four-sample extensions cover every corner (`checks/cyclic-lesson-probe.json`). As a small witness against role/corner coupling, exact overrides successfully generate a bottom-right union with `b_subset_a` and split-origin masks, and the 54,090-draw matrix reports no incompatibility.

Remaining restriction is explicit rather than hidden: inputs use connected color-1/color-2 objects, one corner legend, overlapping unequal masks, and bounded normalized boxes. The finite rival census and these restrictions do not prove universal induction.

## Current parametric family: native ready, owner acceptance pending

`workspace/parametric/adapter.py` exposes `component_policy=all|largest`. The
`all` source is byte-identical to the canonical rule. `largest` computes the
normalized Boolean result before choosing its largest 4-connected component by
cell count; ties use bbox row, column, then row-major discovery. Only selected
cells are rendered, preventing an enclosed losing component from surviving a crop.
Production `generator.py` and its canonical Racket authority remain unchanged.

The new sampler constructs disconnected intersections as well as varied XOR
results, retaining connected-growth/subset cases. It supports 3–6 demonstrations
and 1–4 distinct prefix-stable queries; three demos teach the three independent
control meanings. Same seed/count inputs are identical under both settings.
Demonstrations are selected before queries against 10 `all` and 15 `largest`
rivals, including every wrong legend permutation, wrong alignment, component
ranking/connectivity and opposite ties. Candidate search is bounded; failure is
explicit, never a shorter episode or a relabeled success.

Evidence: 42 focused tests passed (`checks/fb7f02aa9ab0/tests-final.json`). The
source-bound task-local `workspace/parametric/evidence/current/private/evidence.json`
records 8 episodes (seeds 0/17, demos 3/6, both policies), 68 executed episode
labels, 450 executed rival/mirror checks, 12 labels on six minimum/maximum-size
inputs, zero generation failures and zero surviving declared rivals. The 30×30
stress uses 203–243 cells per operand, with 28×13 or 13×28 occupied bounds; the
large XOR stress has seven result components. Eight one-current-query public
files passed prefix, metadata/answer-invariant ID and strict export checks.

Native qualification passed both settings and two seeds in
`checks/fb7f02aa9ab0/qualification/qualification.json`, with sibling protected
`execution.json`. A is the control-selected Boolean operation; its intermediate
is the resulting cell mask/components; B ranks those pieces and crops the
winner. Two protected counterfactual replays replace A with union while holding
B fixed, changing both final outputs. The XOR witness has component sizes
1,5,1,1,1,1,1,7; see `checks/fb7f02aa9ab0/causal-final/witness.json` and `replay.json`.

Limits: finite synthetic geometry, finite rivals/seeds, no universal induction
claim or measured learning benefit. The new family is reviewer-ready, not yet
owner-accepted. Integrate the returned source/inventory, qualify the exact live
bytes and run native acceptance before using the parametric production API.
Canonical regression batteries were not rerun because canonical source is unchanged.
