# Working notes: 76aff6297765

## Native parametric family: current review-777936179039e2be

The separate `workspace/parametric/adapter.py` now supports episode-fixed
`selection=all|largest`. `all` returns the exact canonical Racket program bytes;
`largest` computes the aligned joint-zero mask and retains all largest
four-connected components, including ties. Production `generator.py` and the
canonical authority are unchanged.

Two constructed demonstrations suffice: same-foreground tied maxima with a
smaller diagonal neighbor; then distinct-foreground compact maximum versus a
smaller component with a larger bounding box. Both source panels have misleading
zero components, so selecting before intersection is observably wrong. Shared
scaling and independent dihedral transforms/palettes retain these witnesses.
Additional demonstrations and queries vary occupancy density and topology.
Counts are independently 2–6 demos and 1–4 queries, normally 3 and 4. The query
prefix is count-independent. One or two contiguous separator rows are admitted
by the separate sampler; the unchanged canonical `zip-halves` semantics supports
both. Four-query input sizes include 7×3, 21×23, 29×29 and substantive 30×30.

Current checks:
- 15 focused tests passed, including all five canonical labels, strict arguments,
  independent counts, ties, wrong order, private-field isolation and first-turn
  identity between single-query and four-query requests.
- `workspace/parametric/evidence/current/self-review.json`: 217 protected Racket
  executions passed. At seeds 0 and 17, two demos refuted 19 incorrect named
  rivals for `all`, 24 for `largest`; the intended independent control survived.
  Empty/single/full/tied masks, 30×30 labels and mask interventions passed.
- The separately labeled Python diagnostic passed 192 episodes / 1,472 pair
  claims across seeds 0–31, demo counts 2/3/6 and both settings, with no failed
  draws or duplicate inputs in that bounded sample. It is not a Racket replay of
  all 1,472 pairs. Fixed-threshold rivals are covered in this diagnostic and by
  the two demonstrations' reversed retained/discarded-size relationship.
- Native `checks/76aff6297765/qualification/` qualified four jobs: both settings,
  seeds 0/17, three demos and four queries; 28 labeled pairs, 40 Racket executions.
- `checks/76aff6297765/causal/witness.json` and `causal/replay.json` retain two
  source-bound qualified demonstrations where selecting top-panel components
  before intersection changes the final answer. Both programs were executed
  and replayed by the native protected witness helper.

The prototype inventory is `workspace/parametric/evidence/manifest.json`.
Public first-turn examples and a separate four-query private controller index
are in `checks/76aff6297765/examples/`. The public checker passed two files;
query answers, settings, program, seed and future inputs are absent.

Decision: native reviewer-ready; owner exact-source acceptance remains pending.
The owner's integration workflow must requalify and freshly accept these live
bytes. No production approval was changed and no training data was admitted.
Finite rival evidence does not prove arbitrary-rule uniqueness or model gains.
The two teaching motifs have bounded structural variety; queries have broader
random topology. Arbitrary query rotations are not part of this adapter's
contract. Next action: integrate this delta, then run native owner admission.

## Current rule and authority

The input is two equal zero-background panels separated by one full row of colour 7. The output has the panel dimensions and contains colour 8 exactly where the aligned cells in both panels are 0; the other three joint zero/foreground relations map to 0. `RULE_HASH = 5b347fef0b78` is pinned to the canonical Racket program. This review did not change any Racket authority text.

## Review decision (review-57b3034aac19ed74)

The selected baseline (`generator.py` SHA-256 `9d5bd7b9cba9feb8ed1dcbda2253b4625a03bdef4c4968c706d00ea96377cea5`) passed the native battery but had a teaching ambiguity that the declared lesson hook missed. At seed 91, hard difficulty, schedule start 0, a profile-gated rival used the intended rule on canonical or same-foreground scenes and otherwise emitted the correct number of 8s as a row-major prefix. It fit all three baseline demonstrations and disagreed on the distinct-colour query. The exact retained baseline lesson is `counterexamples/profile-gated-count-shortcut/baseline.json` and the before probe is `checks/selected/profile-gated-count-shortcut-before.json`.

The repair uses a six-slot cyclic schedule with two strict canonical anchors, two same-foreground controls, and two distinct noncanonical controls. A lesson contains five demonstrations and one query. Therefore every query rotation leaves at least one same-foreground witness against `equal_cells` and at least one distinct noncanonical witness against the profile-gated rival. Every ordinary grid also contains all four aligned occupancy relations, and the both-zero locations are forced not to be a row-major prefix.

`CANONICAL_SHORTCUTS` now names only rivals that actually fit all five canonical pairs: `equal_cells` and `profile_gated_count_only`. Every semantic witness names a rival it demonstrably refutes; profile-presence counters were removed from `SEMANTIC_WITNESSES` because they were not discriminating witnesses. Exact controls are `panel_h`, `panel_w`, `top_color`, and `bot_color`; `observe_overrides` recovers all four.

## Verification on final generator bytes

Final `generator.py` SHA-256: `afaf146eed640aa8aa6e1f3ac3bfa3178fa3b1c04d2f1349d7e655c304f27d7d`.

- Native after battery: 12/12 stages green (`checks/after-final/checks/76aff6297765_after_battery_summary.json`).
- Focused portable tests: 76/76 passed (`checks/task-tests-green-4/result.json`).
- Exact override matrix: 25,380/25,380 accepted, 282 cases across three bands, zero findings (`checks/after-final/checks/76aff6297765_after_override.log`).
- Production census: 300/300 lessons materialized, 1,800 labelled pairs, 1,800 unique inputs, zero ambiguity or scoring/materialization errors. All 1,800 query rotations were also unambiguous (`checks/lesson-census-final.json`).
- Exhaustive finite schedule probe: 486 cyclic lesson windows, 2,916 query rotations, 20,412 declared-competitor checks, and all 16 pointwise Boolean occupancy rules on 2,916 grids; zero errors or row-major collisions (`checks/relation-curriculum-probe-final.json`).
- Post-repair visible-only solve was prepared from the same generator hash and passed 5/5 visible demonstrations on the first retained attempt (`solve/summary.json`).

## Limits and open findings

The finite probes establish the declared rivals and the complete six-slot schedule over the sampled seed/band set; they do not prove unique induction against every imaginable rule. The grammar intentionally restricts each panel to one foreground colour and panel sizes 3..8. Arbitrary exact colour overrides may collapse a scheduled profile (for example equal requested colours in a distinct slot); overrides are treated as exact input controls rather than curriculum promises. No prior return was used as a repair lead; the defect was reproduced directly from the pinned selected baseline.
## Current reviewer considerations

Source SHA-256: `afaf146eed640aa8aa6e1f3ac3bfa3178fa3b1c04d2f1349d7e655c304f27d7d`.

# Decisions for 76aff6297765

## D1 — Preserve the canonical rule and authority text

- **Prior choice:** The selected source already mirrored the canonical aligned double-zero rule and pinned `RULE_HASH = 5b347fef0b78`.
- **Original rationale:** Unknown beyond the current source and canonical ledger; no prior return was used as a lead.
- **Probe:** The before battery's rule smoke and authority sync both passed, and all five canonical pairs matched the Python mirror.
- **Decision:** Keep the Racket authority unchanged and repair only generation, curriculum metadata, semantic rivals, tests, and tools.
- **Rejected alternative:** Editing Racket to match a shortcut or a distribution artifact. That would change a correct task rather than repair its teaching data.
- **Failure mode/limit:** The Python mirror remains diagnostic; final labels are still verified by Racket-backed checks.

## D2 — Replace the four-slot/three-demonstration schedule with a six-slot/five-demonstration cycle

- **Prior choice:** The baseline used one canonical anchor, two same-foreground scenes, and one distinct scene, with three demonstrations and one query.
- **Failure:** At seed 91, hard, start 0, the query was the only distinct scene. A profile-gated count-only rival fit all three demonstrations and disagreed on the query while `lesson_identifiable` returned no reason. Evidence: `checks/selected/profile-gated-count-shortcut-before.json`.
- **Alternatives considered:**
  1. Keep three demonstrations and reject unlucky query positions by resampling.
  2. Use a five-slot cycle with one copy of each decisive profile.
  3. Use six slots with two copies of each of three profile families.
- **Decision:** Use two canonical anchors, two same-foreground controls, and two distinct noncanonical controls; expose five as demonstrations and hold out one query.
- **Rationale:** Any rotation leaves at least one same-foreground and one distinct witness. This is deterministic, easy to audit, and avoids query-position-specific resampling.
- **Probe:** All 486 sampled cyclic windows and all 2,916 query rotations passed the final finite probe; the production census passed 300 lessons and 1,800 rotations.
- **Limit:** Five demonstrations are more expensive than three. The checks cover declared rivals and finite sampled seeds, not every possible hypothesis.

## D3 — Treat `equal_cells` and a profile-gated count-only rule as canonical shortcuts

- **Prior choice:** `CANONICAL_SHORTCUTS` copied all declared semantic rivals, even though five of them failed every canonical pair.
- **Alternatives considered:** Remove the declaration entirely, or list only `equal_cells`.
- **Decision:** Compute and test the actual canonical fit; declare exactly `equal_cells` and `profile_gated_count_only`.
- **Rationale:** Both fit all five canonical pairs and therefore require generated counterexamples. The profile-gated rule is stronger than a plain count-only rule because it can behave correctly on all canonical and same-colour evidence.
- **Probe:** `workspace/probe_relation_curriculum.py` derives the fit matrix from the actual declarations. Focused tests fail if the declared and actual sets diverge.
- **Limit:** Other undeclared canonical-fitting algorithms may exist.

## D4 — Make every ordinary grid locally diagnostic

- **Prior choice:** Generated grids contained all four occupancy relations, but the both-zero cells could accidentally coincide with a row-major prefix.
- **Alternatives considered:** Rely only on lesson-level profile diversity, or reject colliding draws and redraw from scratch.
- **Decision:** Preserve relation counts while swapping state positions when necessary so the both-zero set is never a row-major prefix.
- **Rationale:** Every labelled pair independently refutes the simple count-only placement rival without changing task semantics or marginal relation counts.
- **Probe:** The focused regression list includes known colliding baseline draws. The final probe found zero collisions across 2,916 generated grids and enumerated all 16 pointwise Boolean occupancy tables per grid; only the intended mask fit.
- **Limit:** This addresses one spatial placement shortcut, not arbitrary shape-dependent placements.

## D5 — Keep four exact observable axes and fail closed

- **Choice:** `panel_h`, `panel_w`, `top_color`, and `bot_color` remain the only public controls. Unknown controls raise `ValueError`; `observe_overrides` recovers all four from the returned grid.
- **Rationale:** These axes are directly visible and independently useful. Schedule profile is derived from sample index rather than advertised as an override, avoiding a second source of truth.
- **Alternative rejected:** Advertise joint-state counts or schedule profile as controls. Exact arbitrary counts would complicate feasibility at small areas, and exact profile semantics can conflict with exact colour overrides.
- **Probe:** The final override stage accepted 25,380/25,380 draws over 282 cases and three bands with zero findings.
- **Failure mode/limit:** Exact colour overrides intentionally take precedence over curriculum category promises; for example, requesting equal colours in a nominal distinct slot can collapse that category. Such calls are control tests, not production lesson assembly.

## D6 — Keep only discriminating semantic witnesses

- **Intermediate choice:** `strict_canonical_anchor` and `broadened_geometry_or_palette` were included as semantic witnesses even though they named no rival disagreement.
- **Failure:** The strict semantic gate correctly marked both weak and exited non-green.
- **Decision:** Remove them from `SEMANTIC_WITNESSES`; strict-profile and distribution coverage remain measured by dedicated battery stages. Require every semantic witness name to appear in `WITNESS_RIVALS`.
- **Probe:** A test was first added and observed failing with exactly those two extra names; after the change 76/76 task-local tests passed and the semantic gate turned green.
- **Limit:** Presence metrics are still useful, but they should not be presented as counterexample witnesses.

## D7 — Add a portable, source-bound finite probe

- **Choice:** Add `workspace/probe_relation_curriculum.py` plus focused tests.
- **Rationale:** The shared census samples production lessons but does not enumerate all starts in a small deterministic cycle or all 16 pointwise truth tables.
- **Implementation decision:** Load the staged package when present and fall back to the sibling generator source in a direct repository checkout.
- **Probe:** The fallback was developed test-first: the test failed when `_load_generator` was absent, then passed after implementation. Final run: 486 windows, 2,916 rotations, 20,412 competitor checks, 2,916 grids × 16 truth tables, zero errors.
- **Limit:** The tool is task-specific and finite; Racket remains the output authority.

## D8 — Preserve evidence rather than erase failed iterations

- **Choice:** Retain the baseline ambiguity, initial 47-test red run, missing-tool red run, loader-fallback red run, weak-witness red run, and the interrupted/intermediate battery directories.
- **Rationale:** They establish the red-green sequence and distinguish task defects from controller interruptions.
- **Limit:** Only decisive evidence should be packaged to stay within the return budget; complete local directories remain available in the working packet.
