# Working notes: 24bb2221ca5c

## Baseline diagnosis

The imported v2.1.0 generator produced only perfect 3–5-cell rectangular outlines. That was enough for the selected Racket rule to fire, but it taught several simpler rules equally well—especially “fill every zero inside each component bounding box” and “fill rectangular frames only.” Its texture/palette axes were inert or mixed negative fixtures into the lawful domain, exact override provenance was missing, unknown override names were accepted, `RULE_HASH` was absent, exact canonical-profile support was sparse, and no semantic contract was declared.

Baseline battery evidence remains under `checks/before/`.

## First repair: v3.0.0

Version 3.0.0 kept frequent canonical frames and added two minimal topology controls: a one-gap side-open decoy and a closed frame with an outward spur. A deterministic three-profile schedule guaranteed canonical support and witnesses against six rival rules. Exact observable axes replaced fake aliases. `self_check`, `strict_canonical_like`, `rule_mirror`, semantic witnesses, named rivals, witness-to-rival claims, and `lesson_identifiable` made the intended lesson executable.

The selected Racket authority was not edited. `RULE_HASH = "514c258ab731"` pins every generator revision to it.

## Second repair: v3.1.0

The first repair still taught one hole per component and one component per color. Version 3.1.0 added a two-chamber spurred component and a disconnected same-color ring. That refuted `fill_one_hole_per_component` and `merge_same_color_bboxes`, bringing the contract to eight rivals.

## Third repair: v3.2.0

A 900-sample adversarial probe found that all 1,800 generated holes in v3.1.0 were rectangular and every deliberate opening was a side opening. Thus two further canonical-fitting shortcuts survived:

- `eight_connected_holes`: use 8-neighbor background escape rather than 4-neighbor escape;
- `rectangular_holes_only`: ignore any enclosed region that is not rectangular.

Version 3.2.0 makes both distinctions observable:

- `gap_contrast` pairs a corner-gap positive with a side-gap negative. Diagonal contact through the corner is not a 4-neighbor escape route.
- `topology_stress` uses a dense two-cavity mass with at least one L-shaped hole and an outward spur, plus a disconnected ring in the same color.

The contract now has ten executable rivals and ten matching witnesses. Every default three-example window refutes all ten.

## Test-first record

Round three began by adding eight assertions for the new semantics and tool contract. The red run produced eight expected failures because v3.1.0 rejected the fixtures, lacked the witnesses/rivals, and lacked the exact verifier. Implementation then made the same suite pass; the final focused suite contains 18 passing tests.

Evidence:

- `checks/round3_tdd_new_semantics_red.log`
- `checks/round3_tdd_new_semantics_green.log`
- `checks/round3/custom/pytest_v32.log`
- `checks/round3/custom/pytest_v32.xml`

## Reusable probes

- `workspace/profile_probe.py` samples complete three-example windows, validates each scene, checks lesson identifiability, records witness grids, retains the first counterexample for every rival, and counts corner gaps, hole shapes, hole counts, and color reuse.
- `workspace/verify_shortcut_counterexample.py` executes the side-gap/bbox disagreement through canonical Racket.
- `workspace/verify_topology_counterexamples.py` executes the multi-hole/same-color fixture through canonical Racket.
- `workspace/verify_connectivity_shape_counterexamples.py` executes exact corner-gap and L-cavity fixtures through canonical Racket and compares the new rivals.
- `workspace/generator_v2_1_0_baseline.py` preserves the imported baseline.

## Current measured state

Round-three evidence at the time of writing:

- 18 task-local tests pass;
- a 432-sample / 144-window profile probe has zero failures, sees all ten witnesses, and refutes all ten rivals;
- the probe contains 144 corner-gap scenes, 144 nonrectangular-hole scenes, 144 multi-hole scenes, and 144 same-color-component scenes;
- the semantic gate accepts all five canonical inputs, verifies all ten witness/rival claims, and marks 12/12 lessons identifiable;
- an 864-case boundary override matrix has zero generation, validation, dimension, or observability failures;
- exact Racket/Python parity holds on both new counterexamples, with 9 disagreement cells for the 8-connected rival and 3 for the rectangular-hole-only rival;
- the complete battery has all 12 stages green.

Repository-wide and clean-replay results are recorded in the return-level `REVIEW.md` and `RESULTS.json` only after their final runs.

## Remaining limits

The lawful grammar is a controlled teaching subset, not the entire authority domain. It does not sample arbitrary concave loops, thick walls, three or more holes, nested components, internal colored islands, touching ownership cases, overlapping bboxes, or another-color object inside a hole. The periodic three-profile cadence is reliable for lesson construction but less natural than an unconstrained corpus distribution. The corner/side gap controls and dense cavity mass are still finite template families. These exclusions keep generated scenes auditable and avoid treating authority overwrite order as settled semantics.
## Current reviewer considerations

Source SHA-256: `e857d9cf20ec790738140a995e6987bfafc85080b6f871acef89e552312aac5e`.

# Decisions — generator 24bb2221ca5c

## 1. Interpret the rule as component-local enclosed-hole filling

**Original rationale:** The imported notes described hollow rectangles becoming solid rectangles because every official demonstration is rectangular. The selected Racket program is broader: for each same-color 4-connected component, it fills bbox-local zero regions that cannot reach the component bbox boundary by 4-neighbor motion.

**Decision:** Preserve exact rectangular anchors while teaching the broader topological behavior already executed by the unchanged authority.

**Alternatives:** Keep the rectangle-only story; rewrite the Racket rule as rectangle completion; immediately sample arbitrary free-form loops.

**Probe:** All five canonical pairs remain accepted, and rule-smoke plus three exact counterexample tools compare the Python mirror with real Racket.

**Limit:** The generated grammar remains a strict, auditable subset of the authority domain.

## 2. Keep a deterministic three-profile lesson window

**Decision:** `sample_index mod 3` schedules `canonical_pair`, `gap_contrast`, and `topology_stress`; `EXAMPLES_NEEDED` remains 3.

**History:** v3.0.0 used `open_decoy` plus `irregular_broad`; v3.1.0 replaced the latter with multi-hole/same-color stress; v3.2.0 strengthens both noncanonical profiles without increasing lesson length.

**Alternatives:** Independent random profiles; four or five demonstrations; reserve stress profiles for hard mode.

**Why:** Three examples are enough to combine canonical fidelity, a close connectivity contrast, and a dense positive topology case. A deterministic window prevents unlucky lessons from omitting rule-identifying evidence.

**Probe:** The 432-sample probe checked 144 consecutive windows with zero surviving rivals. The semantic gate marked 12/12 lessons identifiable, 4/4 per band.

**Limit:** The cadence is curriculum-shaped rather than a natural corpus distribution. Exact overrides may alter profile contents while remaining lawful.

## 3. Keep exact canonical anchors frequent

**Decision:** `canonical_pair` uses two exact rectangular frames, canonical colors, cycles official-neighborhood dimensions, and forces one frame to touch the canvas border.

**Original problem:** v2.1.0 had only 2/60 exact canonical-profile support.

**Alternatives:** Randomize all dimensions; duplicate official grids; place every frame away from edges.

**Why:** Scheduled anchors prevent semantic broadening from starving the official neighborhood; border contact also refutes edge-skip behavior.

**Probe:** `strict_canonical_like` accepts all five official inputs and classified 193/600 semantic-gate draws as strict-canonical.

**Limit:** The anchor cycle is representative rather than exhaustive.

## 4. Pair a corner-gap positive with a side-gap negative

**Decision:** `gap_contrast` places one rectangle missing a corner and one otherwise similar rectangle missing a non-corner side cell. Under 4-connectivity, the corner gap is only a diagonal contact and the hole remains enclosed; the side gap provides a 4-neighbor escape and remains unfilled.

**Original state:** v3.0–v3.1 used only side-gap negatives, so an 8-connected background flood agreed with every generated example.

**Alternatives:** Keep only the side-gap control; use random noise; use a wider opening; introduce touching components.

**Why:** The paired scene changes one local topological fact and makes the connectivity convention directly observable without requiring a new lesson slot.

**Probe:** `workspace/verify_connectivity_shape_counterexamples.py` reports exact Racket/Python agreement and 9 differing cells for the 8-connected rival. The profile probe observed 144 such scenes; the semantic gate verified the claim 60/60 times.

**Limit:** Both controls remain rectangle-derived; irregular open contours are not yet sampled.

## 5. Teach multiple holes and nonrectangular hole shape together

**Decision:** The main stress component is a dense bordered mass with exactly two cavities, at least one L-shaped cavity, one remaining colored interior separator, and an optional outward connected spur.

**Original progression:** v3.0 had one hole per component. v3.1 added two rectangular chambers. That still allowed “fill rectangular holes only.”

**Alternatives:** Arbitrary concave loops; three-hole grids; nested rings; thick walls; internal islands.

**Why:** A dense cavity mass is compact, exactly classifiable, and simultaneously teaches hole enumeration, nonrectangular shape invariance, and preservation of bbox-exterior zeros from the spur.

**Probe:** The profile probe observed 144 multi-hole and 144 nonrectangular-hole scenes. The exact rectangular-hole rival differs from Racket at 3 cells; one-hole-only differs at 6 cells on the retained fixture.

**Limit:** The family currently uses exactly two cavities and a small set of cavity layouts.

## 6. Define objects by 4-connectivity, not color identity

**Decision:** `topology_stress` also contains a disconnected closed ring in the same off-canonical color as the dense cavity component, separated by a one-cell moat.

**Original state:** v3.0 gave every disconnected component a distinct color.

**Alternatives:** Retain unique colors; allow touching same-color components; use overlapping bboxes or nested components.

**Why:** Reused color directly forces component extraction while the moat isolates that lesson from touching/ownership ambiguity.

**Probe:** The 432-sample probe observed 144 reused-color scenes; `merge_same_color_bboxes` disagrees with exact Racket output at 5 cells on the retained topology fixture.

**Limit:** Touching and overlapping ownership cases remain excluded.

## 7. Keep palette behavior observable

**Decision:** `canonical` uses the official color set; `broad` guarantees a closed target in color 1 or 8. Stress components share that off-canonical target color.

**Original problem:** v2.1.0 exposed four palette labels whose outputs were byte-identical.

**Alternatives:** Keep undocumented warm/cool aliases; remove the axis; uniformly randomize all colors.

**Why:** Two falsifiable modes are better than inert labels. Broad positives refute canonical-color-only behavior while canonical support remains frequent.

**Probe:** `observe_overrides`, the built-in override stage, and the 864-case boundary matrix recover and verify both modes.

**Limit:** Palette balance is intentionally coarse.

## 8. Keep only five exact override axes

**Decision:** The public axes are `grid_h`, `grid_w`, `n_frames`, `n_open_decoys`, and `palette_kind`. Unknown keys raise `ValueError`; non-dimensional axes are recoverable from the materialized grid.

**Original problem:** v2.1.0 exposed aliases, locked pseudo-axes, and negative fixtures inside the lawful domain.

**Alternatives:** Preserve compatibility aliases; expose topology subtype as an axis; treat unknown keys as no-ops.

**Why:** A small exact contract is easier to falsify and maintain. Topology remains curriculum structure rather than a caller-selected subtype.

**Probe:** The full override gate accepted 11,520/11,520 draws and rejected unknown keys. The independent boundary matrix covered 864 min/max and profile-crossing cases with zero failures.

**Limit:** Removed aliases are a breaking change for hypothetical external callers; no packet caller used them.

## 9. Use difficulty for geometry, not semantic availability

**Decision:** Difficulty changes packing and dimensions; every band still receives every profile and every witness.

**Alternatives:** Put multi-hole or nonrectangular cases only in hard mode; vary rule semantics by band; ignore difficulty.

**Why:** Rule-identifying evidence should not disappear from easy or medium training. Scale can change visual complexity without changing the concept.

**Probe:** All ten witnesses fired across the semantic census, and every band had 4/4 identifiable lessons.

**Limit:** Difficulty mostly measures geometry rather than ownership ambiguity or hole count.

## 10. Retain a one-cell moat

**Decision:** Distinct components may reuse color but must remain Chebyshev distance greater than one.

**Alternatives:** Permit diagonal contact, edge contact, or overlap.

**Why:** The moat keeps component extraction and color-reuse evidence unambiguous while the new corner-gap example separately teaches diagonal background connectivity.

**Probe:** `self_check` rejects moat violations, and the grammar stage passed.

**Limit:** The curriculum does not yet teach component ownership under contact.

## 11. Make every intended distinction executable

**Decision:** `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `rule_mirror`, and `lesson_identifiable` form an executable semantic contract.

**History:** v3.0 declared six rivals; v3.1 declared eight; v3.2 declares ten by adding `eight_connected_holes` and `rectangular_holes_only`.

**Alternatives:** Explain semantics only in prose; rely only on output diversity; add examples without explicit rival tests.

**Why:** Diversity cannot prove identifiability. Executable rivals turn each claim into a falsifiable check and expose canonical ambiguity explicitly.

**Probe:** The semantic gate reports 10/10 witnesses firing, 10/10 claims verified, no competitor surviving an identifiable lesson, and 12/12 identifiable lessons.

**Limit:** The rival set is strong but not exhaustive; future audits can add new competitors without changing the authority.

## 12. Extend task-local evidence and future-agent tools

**Decision:** Retain small probes next to the generator rather than relying only on the monolithic battery.

**Tools:**

- `profile_probe.py` checks complete windows, witnesses, rivals, overrides, and topology counts;
- `verify_shortcut_counterexample.py` checks the side-gap/bbox disagreement;
- `verify_topology_counterexamples.py` checks one-hole and color-merge shortcuts;
- `verify_connectivity_shape_counterexamples.py` checks 4-vs-8 connectivity and nonrectangular cavities;
- `generator_v2_1_0_baseline.py` preserves the imported implementation.

**Alternatives:** Keep ad hoc shell snippets or trust only aggregate stage verdicts.

**Why:** Compact exact reproducers are easier for future agents to understand, rerun, and extend.

**Probe:** All tools have focused tests, and both new exact fixtures match Racket byte-for-byte.

**Limit:** The tools deliberately target the declared grammar, not every possible authority input.

## 13. Preserve the selected authority

**Decision:** Do not modify the Racket rule; keep `RULE_HASH = "514c258ab731"` pinned.

**Alternatives:** Narrow the authority to rectangle fill or alter its ownership behavior.

**Why:** The authority passes every official pair. The identified defects were in what the generator taught, not in canonical correctness.

**Probe:** Authority-sync and 120/120 rule-mirror parity passed. The sync report still isolates one pre-existing archival divergent copy outside the selected authority set.

**Limit:** The unchanged authority's overwrite order for nested other-color objects remains intentionally untaught.

## 14. Exclude nested and overwriting scenes for now

**Decision:** Do not generate another-color object inside a hole, nested rings, overlapping bboxes, or ambiguous touching ownership.

**Alternatives:** Treat current execution order as intended semantics; rewrite the authority first; generate cases and accept order dependence.

**Why:** The current authority may overwrite pre-existing colors while processing an enclosing component. Teaching that behavior without an explicit product decision would turn an implementation detail into a learned rule.

**Probe:** Scene validation and slot/moat construction exclude these cases.

**Limit:** The generator therefore does not cover the full operational domain of the authority.

## 15. Stop after eliminating the strongest remaining observed shortcuts

**Decision:** End this pass after test-first support for corner-gap and nonrectangular-cavity semantics, exact Racket witnesses, full battery success, repository regression replay, and clean package replay.

**Alternatives:** Continue broadening indefinitely into arbitrary topology.

**Why:** This pass removes two concrete canonical-fitting rules discovered by measurement. Further broadening now enters ownership and arbitrary-shape questions with higher ambiguity and lower immediate return.

**Probe:** The before probe demonstrated both gaps; the v3.2 probes and semantic battery demonstrate their removal.

**Limit:** A later adversarial pass may still identify another finite rival family; the contract is designed to accept such additions.

## Current parametric admission review — 2026-10-24

**Decision:** retain the production generator and selected canonical authority unchanged. Add a task-local native adapter with one episode parameter, `fill_policy`, whose values are canonical `all`, `largest_hole_area`, and `most_holes`. The selective variants preserve component extraction and enclosed-region reasoning, then make an input-dependent ranking decision before filling.

**Teaching repair:** each mandatory scene contains three different selector winners: the greatest enclosed area, the greatest hole count, and the greatest bbox area belong to different components. The first two demonstrations reverse component reading order and distinguish every declared setting. The retained finite audit also attacks identity, first/last closed component, largest bbox area, and smallest enclosed area; none survives the visible demonstrations across seeds 0 and 17.

**Reversal:** the first prototype copied archival `racket_target.raw_code` (30,826 bytes). Native qualification correctly rejected it because the catalog authority is `racket_target.target_code` (1,720 bytes, SHA-256 `514c258ab731e4505bfca2101754e3b65d525218243f63ac16632c6b87ef2744`). The adapter and regression test now bind that exact canonical program.

**Causal dependency:** Step A computes component-local enclosed regions, total enclosed area, and hole count. Step B ranks components using those measurements and fills the selected component. The source-bound witness substitutes bbox area for Step A's enclosed-area intermediate, selects another component, and changes the final protected-Racket output.

**Measured result:** 29 focused tests and 29 packet-level changed-target tests pass. Native qualification covers three settings, two seeds each, six jobs, and 78 protected-Racket evaluations. The manifest is current; the protected-Racket witness replay passes.

**Limit / next action:** this is finite reviewer evidence, not universal uniqueness or measured training gain. The owner must integrate the exact patch, re-run native qualification and fresh acceptance replay, assess the causal interpretation, and only then accept the family. No variant is currently training-admitted. Optional peers `21c9650143ce` and `7f181d3b0012` were intentionally left unrun after MAIN completion.
