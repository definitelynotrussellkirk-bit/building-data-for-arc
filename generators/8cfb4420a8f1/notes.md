# Current notes: 8cfb4420a8f1

## Intended rule

Row 0 contains exactly one nonzero color selector. Preserve that marker, erase every occurrence of its color below row 0, and preserve all other cells. The canonical Racket authority is unchanged and remains pinned by `RULE_HASH=506219441313`.

## Current generator decision — version 3.1.0

- `seed`, `sample_index`, and every integer override are exact integers; booleans, floats, strings, and negative sample indices are rejected.
- Ordinary distractor colors are connected objects rather than scattered singleton fields. The primary object intersects the marker column; true targets avoid that column.
- The modal non-marker color, marker-column decoy, multiple distractor colors, and first-body distractor are deliberate shortcut controls.
- Lessons use three demonstrations. The four-profile schedule supplies a canonical anchor and left/center/right guards.
- Exact canonical-profile support is retained in every difficulty band.

## Reversed baseline choices

1. **Scattered distractors → connected objects.** Baseline v3.0.0 produced a disjoint persistent-singleton support from the canonical examples. The retained reproducer is `counterexamples/baseline_disconnected_distractor.json`.
2. **All rivals labeled canonical shortcuts → one verified shortcut.** The baseline `CANONICAL_SHORTCUTS` declaration was invalid. Only `erase_first_nonzero_body_colour` fits every labeled canonical pair; generated scenes explicitly refute it.
3. **Permissive scalar draws → exact scalar contract.** Baseline strict defect lint emitted 144 warnings.

## Final evidence

- Baseline battery: 10/12 green; defect lint and semantic gate failed.
- Final battery on generator SHA `364f56bac1af0e51d05b12c95bb6317e66ef48dd1608d9cd92eff23b9fb20740`: 12/12 green.
- Profile floor: exact 17/60, envelope 21/60, with exact support in all bands.
- Semantic gate: 143/600 strict canonical-like draws, six witnesses each 600/600, 12/12 lessons identifiable, 48/48 smoke rotations unambiguous.
- Larger census: 300/300 production lessons and 1,200/1,200 query rotations unambiguous over 1,200 unique inputs.
- Selected task tests: 55 passed.

## Parametric prototype

`workspace/parametric/` contains an isolated proposed `erase_scope` variant: canonical `body_only` versus `all_occurrences`. The setting is chosen once per episode and exact Racket is executed for labels. It is not part of the selected canonical path.

## Known limits / open findings

- Finite declared-rival checks are not a universal identifiability proof.
- Ordered production lessons remain the intended policy even though sampled rotations pass.
- Exact override `primary_distractor_count=2` uses singleton extras to preserve exact observability.
- Catalog approval and training admission remain maintainer decisions.
- The frozen legacy test fixture still imports `scripts.canonical_profile_gate`; it passes unchanged but should be migrated by the maintainer.

## Prior notes used as leads

Associated notes `GNOTE-003183`, `GNOTE-003184`, `GNOTE-003185`, and `GNOTE-003186` guided inspection of controls, schedule, checker strength, and authority sync. Their old measurements were not reused as current evidence.
## Current reviewer considerations

Source SHA-256: `364f56bac1af0e51d05b12c95bb6317e66ef48dd1608d9cd92eff23b9fb20740`.

# Decisions for 8cfb4420a8f1

## D1 — Reject scalar coercion at the request boundary

**Prior choice:** The baseline used permissive `draw_int` calls and accepted non-exact scalar forms for `seed`, `sample_index`, and integer overrides. The original rationale is unknown; it was likely convenience inherited from shared draw semantics.

**New choice:** Require `type(value) is int` for `seed` and `sample_index`, require nonnegative `sample_index`, and use `ctx.draw_int_strict` for every declared integer axis.

**Why:** A request such as `n_distinct_colors=4.75` was silently accepted. That makes exact-control evidence unreliable and allows training recipes to claim one setting while executing another.

**Alternatives considered:**

1. Keep coercion and document it. Rejected because the axes are explicitly declared as exact integers.
2. Cast with `int(...)` in the generator. Rejected because it preserves silent truncation.
3. Wait for a shared-library change. Rejected for this return because the selected task needed a source-bound repair now; the shared improvement is raised separately as feedback.

**Probes/evidence:** Baseline strict defect lint reported 144 warnings. Focused tests cover booleans, integral floats, fractional floats, strings, and negative sample indices. Final defect lint is green.

**Failure modes/limits:** This is intentionally stricter than Python’s usual `bool`-is-`int` relationship. A caller that previously depended on coercion must now fix its request.

## D2 — Replace scattered distractor pixels with connected objects

**Prior choice:** Baseline v3.0.0 placed the primary distractor as a marker-column cell plus independently sampled cells and placed each extra color as a singleton. The original rationale is not documented; it kept counts easy to control but created a noncanonical texture.

**New choice:** Draw the primary distractor as one exact-size 4-connected region that intersects the marker column. Draw ordinary extra colors as connected dominoes. Retain singleton extras only when the exact override requests the minimum primary count of two, because otherwise the primary count is no longer uniquely observable.

**Why:** The baseline structural diagnostic found disjoint canonical/generated support for persistent singleton markers. On the detector’s 60 generated draws, canonical `persistent_markers` support was `{1,2}` while generated support was `{3,4,5,6,7,8}`. This is a strong spurious morphology cue unrelated to the transformation.

**Alternatives considered:**

1. Copy only the exact canonical shapes. Rejected because it would overfit three examples and collapse useful diversity.
2. Keep scattered pixels and downgrade the warning. Rejected because the mismatch is easy to remove without changing the rule.
3. Use arbitrary connected polyominoes for every color and override. Rejected because exact primary-count observability would be ambiguous at the minimum count.

**Probes/evidence:** `counterexamples/baseline_disconnected_distractor.json` reproduces baseline seed 24000, sample 0, easy. The focused regression verifies the retained grid is disconnected and the same request under v3.1.0 yields a connected distractor. Final defect lint is green.

**Failure modes/limits:** Connectedness is enforced per non-marker color on ordinary defaults, not as a universal law of every exact override. The generator still uses deliberately simple small objects and does not reproduce every possible canonical geometry.

## D3 — Declare only a real canonical shortcut and teach against it

**Prior choice:** Baseline set `CANONICAL_SHORTCUTS = _RIVAL_RULES`, even though identity, erase-modal, erase-marker-column, erase-all, and other rivals already failed one or more canonical pairs.

**New choice:** Keep those programs as `SEMANTIC_RIVALS` / `LESSON_COMPETITORS`, but declare only `erase_first_nonzero_body_colour` as a canonical shortcut. Reserve the first body object as a distractor so every generated scene refutes that shortcut. Add a named witness and a canonical-fit regression.

**Why:** A canonical shortcut declaration is a factual claim that the program fits all labeled canonical pairs. The first-body-color shortcut does; the baseline set did not. Explicitly teaching against the actual ambiguity adds data value instead of merely satisfying schema.

**Alternatives considered:**

1. Declare no canonical shortcuts. Rejected because it would discard a genuine ambiguity visible in all three canonical pairs.
2. Keep the invalid declarations as “possible rivals.” Rejected because the correct container for them already exists: `LESSON_COMPETITORS`.
3. Randomize the first body color and rely on some lessons to refute the shortcut. Rejected because a three-demo lesson could then accidentally leave it alive.

**Probes/evidence:** The canonical-fit test checks every declared shortcut against all labeled canonical pairs. The witness fires on 600/600 semantic draws; the shortcut is refuted in all 300 production census lessons and all 1,200 query rotations.

**Failure modes/limits:** Reserving the first body position as a distractor is a deliberate curriculum control. It does not establish that every other conceivable positional shortcut is impossible.

## D4 — Keep the canonical Racket rule unchanged

**Choice:** Do not edit the selected Racket authority or `RULE_HASH=506219441313`.

**Why:** Canonical examples, the Python mirror, and Racket execution already agreed. Every observed failure was in input distribution, request validation, or semantic metadata—not in the transformation itself.

**Alternatives considered:** Rewriting the Racket source for stylistic synchronization or changing behavior. Both were rejected as unnecessary authority churn.

**Evidence:** Rule smoke, Racket lint, and authority sync are green before and after. The after battery retains the same authority-set SHA.

**Failure modes/limits:** An archival raw-code record remains textually divergent but execution-equivalent; the selected authority is exact and pinned.

## D5 — Retain the ordered three-demonstration curriculum and test rotations separately

**Choice:** Keep `EXAMPLES_NEEDED=3` and the four-profile ordered schedule: canonical anchor, then left/center/right shortcut guards across consecutive starts. Do not claim that the production assembler is unordered merely because rotations pass.

**Why:** Three demonstrations are enough to include canonical support and multiple shortcut controls without bloating lessons. Existing sliding-window tests cover starts 0–11 in all bands.

**Evidence:** The semantic smoke test passed 12/12 materialized lessons and 48/48 rotations. The larger census passed 300/300 production lessons and 1,200/1,200 rotations, with 1,200 unique inputs and zero materialization/scoring errors.

**Failure modes/limits:** The random census is finite and does not enumerate every seed or undeclared rival. External lesson assembly that changes demonstration count or filters examples must rerun the hook and census.

## D6 — Build, but isolate, the `erase_scope` parametric prototype

**Choice:** Prototype one episode-level enum: `body_only` (canonical default) versus `all_occurrences` (also erase the top marker). Choose it once from the deterministic episode seed; materialize and execute exact Racket for the selected setting. Keep it outside the canonical generator path.

**Why:** It is a genuinely small rule variation with the same selector mechanism, and demonstrations can distinguish it directly through marker survival. Input axes such as marker position, palette size, or target count are not rule parameters and were therefore not used.

**Alternatives considered:**

1. Parameterize which row is protected. Rejected as a larger grammar change with weaker canonical motivation.
2. Parameterize erase versus recolor. Rejected because it changes both output palette and rule family.
3. Skip a prototype. Rejected because this task has a clean, testable two-setting extension.

**Evidence:** `checks/parametric/erase-scope-v1/summary.json` covers both settings, two exact Racket hashes, three demonstrations per episode, query presence, Racket/Python parity, and pairwise distinguishability.

**Failure modes/limits:** Only two settings and two deterministic episodes were executed. The prototype deliberately makes the setting easy to infer and is not approved for production.

## D7 — Use prior notes only as leads

**Choice:** Consult associated notes `GNOTE-003183`, `GNOTE-003184`, `GNOTE-003185`, and `GNOTE-003186` for likely controls and authority context, then remeasure the pinned baseline.

**Why:** The duties explicitly distinguish prior claims from current measurements. The prior notes helped target inspection but did not establish the present source state.

**Evidence:** All reported counts point to this packet’s `checks/before`, `checks/after`, or final census artifacts.

## D8 — Preserve honest solve provenance

**Choice:** Finish the pre-repair blind solve with `earlier-exposure=no`, and the post-repair solve with `earlier-exposure=yes` and `reference-consulted=no`.

**Why:** The first solve preceded source inspection; the second necessarily followed it. Both stopped after one general rule passed all visible demonstrations, before masked-query feedback.

**Limit:** Neither solve claims masked-query correctness or model trace/log-probability evidence.
