# Working notes: 4e16917b1bde

## Current rule and domain

The selected rule is unchanged: locate the unique uniform nonzero full-height divider column, retain the input, and copy every non-divider colored source cell to its reflected column across that divider while preserving color. Generated inputs place all source cells strictly on one side, keep every reflected destination in bounds and initially background, and forbid the divider color outside the divider.

## Review decisions (v2.0.0 -> v2.1.0)

- **Reversed balanced-only color counts.** v2.0.0 assigned multicolor sources round-robin, so all color frequencies differed by at most one. The canonical-fitting rival “mirror only colors within one count of the modal color” therefore matched the entire generated pool. v2.1.0 still uses every selected source color but creates a count gap of two whenever mathematically possible; scheduled multicolor lessons pin sufficient `source_cells` to guarantee this witness.
- **Expanded the divider role palette.** The old default sampled only colors 5, 8, and 9. The divider may now use any nonzero ARC color; every fifth unpinned sample retains gray 5 as a canonical color-role anchor. Source colors always exclude background and the divider color.
- **Made exact override types strict.** Integer/color controls reject floats, strings, and booleans rather than silently coercing them. Exact integer boundary combinations remain observable.
- **Aligned canonical profiles with lesson slots.** An intermediate every-fifth size anchor could collide with a multicolor schedule and left the pinned medium profile census at 0/20. The two single-color schedule slots now anchor `(5, 9)` and `(6, 10)`, yielding exact canonical-profile support in every band without erasing multicolor counterexamples.
- **Made semantic evidence executable.** `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `BRANCH_WITNESSES`, `CANONICAL_SHORTCUTS`, and public `LESSON_COMPETITORS` distinguish branch coverage from a verified wrong-rule counterexample. The retained exact witness is `counterexamples/rare-color-shortcut.json`; `workspace/shortcut_probe.py` reproduces it.
- **Made task tests portable.** Tests use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`; the prior fixed `Path(...).parents[1]` lookup failed in the copied task-test runtime.

No prior return was used as a design lead. The canonical Racket source and `RULE_HASH=de4ea202a020` were not changed.

## Final evidence

- Final generator SHA-256: `19182d57656a74f19761ca43b549f3da03a8b46d3bde5cff91d68dc810ee91a2`.
- Battery: all 12 after-repair stages green; see `WORK/checks/after-final/checks/4e16917b1bde_after_battery_summary.json`.
- Portable focused tests: 16/16 pass; see `WORK/checks/task-tests/result.json`.
- Profile floor: exact hits easy 3/20, medium 9/20, hard 6/20.
- Semantic census: all seven witnesses fire; the rare-color rival claim is verified on 60/60 checked firings, with no weak witnesses.
- Override contract: 70,650/70,650 generated draws accepted across 785 cases and three bands, with zero findings.
- Lesson census: 300/300 four-demo-plus-one-query lessons materialized, 1,500 unique inputs, zero production ambiguity, and zero ambiguity over all 1,500 query rotations.

## Known limits

The task is a single reflection operation; `multi_rule_interaction` and `sequential_state` are not applicable. The divider’s geometry supplies contextual structure, but no separate cue changes the transformation, so `contextual_gating` is not claimed. Color values are interchangeable roles inferred from geometry rather than task-defined symbols. The finite rival set and sampled lessons cannot prove unique induction against every imaginable program. Explicit caller overrides can deliberately request balanced counts; the production default and scheduled lessons, not every legal override, provide the rare-color counterexample.
## Current reviewer considerations

Source SHA-256: `19182d57656a74f19761ca43b549f3da03a8b46d3bde5cff91d68dc810ee91a2`.

# Decisions — 4e16917b1bde

## D1 — Preserve the selected rule

**Choice:** Keep the canonical Racket rule and `RULE_HASH=de4ea202a020` unchanged.

**Rationale:** Canonical train/test parity, rule smoke, and authority-sync were already correct. The defects were in sampling, executable teaching evidence, and test portability—not output semantics.

**Rejected alternative:** Add a second operation or special color behavior to make examples harder. That would replace the authoritative task rather than improve its curriculum.

**Failure mode checked:** Python `rule_mirror` equals all three canonical outputs and the selected Racket output on the retained counterexample.

## D2 — Counter the strongest canonical-fitting shortcut

**Original choice:** Round-robin multicolor assignment kept each source-color count within one of the modal count.

**Problem:** The rival “mirror only colors within one count of the modal color” fits all three canonical demonstrations (which are single-color) and every old generated example. A learner could ignore genuinely rare colors without penalty.

**New choice:** Use all selected colors and require a frequency gap of two whenever `source_cells >= n_distinct_colors + 2`; pin sufficient cells in multicolor teaching slots. Declare the rival in `SEMANTIC_RIVALS`/`CANONICAL_SHORTCUTS`, connect it to `strong_color_frequency_skew`, and expose lesson competitors publicly.

**Evidence:** `generators/4e16917b1bde/counterexamples/rare-color-shortcut.json` records an exact lawful 5x9 input. The selected Racket rule mirrors the singleton color 3 to `(4,6)`; the rival leaves that cell zero. `workspace/shortcut_probe.py` verifies canonical fit 3/3, validator acceptance, Python/Racket parity, and the differing cell. The final semantic gate verifies the rival claim 60/60; the 300-lesson census refutes it 100/100 in each band in production and every query rotation.

**Limit:** Exact overrides may intentionally request configurations where a two-count gap is impossible. That is legal axis control, not the production teaching distribution.

## D3 — Broaden divider colors without losing canonical anchoring

**Original choice:** Default divider colors were limited to `{5,8,9}`.

**New choice:** Sample every nonzero color `1..9`, while forcing divider color 5 every fifth unpinned sample.

**Rationale:** The rule identifies the divider geometrically; limiting its color permits a color-ID shortcut. Periodic gray retains canonical color-role familiarity without making gray necessary.

**Probe:** A 360-sample focused test observes all nine divider colors and checks every fifth sample is gray. The source palette excludes the chosen divider color.

**Rejected alternative:** Remove gray anchoring entirely. This improves invariance but needlessly reduces canonical color-role support.

## D4 — Strict exact-control types

**Original choice:** `int(...)`/color drawing paths accepted coercible floats, strings, and booleans.

**New choice:** Reject non-`int` raw values for integer and color axes; `None` remains unpinned.

**Rationale:** An “exact” override must not silently change type or interpret `True` as color/count 1.

**Probe:** Focused tests cover representative float/string/bool cases. The final override gate accepts 70,650/70,650 draws over 785 override cases and all three bands.

## D5 — Canonical profile anchors follow compatible schedule slots

**Intermediate failed choice:** Anchor canonical dimensions every fifth sample while preserving the independent color-count schedule.

**Observed failure:** Exact profile support fell to easy 1/20, medium 0/20, hard 3/20 because size-anchor residues rarely coincided with the two single-color slots. Retained failure: `checks/after/checks/4e16917b1bde_after_profile_floor.json`.

**Final choice:** Assign `(5,9)` and `(6,10)` to lesson slots 0 and 1, which are already single-color, unless the caller pins size or color count.

**Evidence:** Final exact-profile counts are 3/20 easy, 9/20 medium, 6/20 hard (`checks/after-final/checks/4e16917b1bde_after_profile_floor.json`). This preserves all multicolor shortcut-rebutting slots.

## D6 — Four ordered demonstrations, with rotation robustness measured

**Choice:** Retain `EXAMPLES_NEEDED=4` and the eight-slot cyclic schedule. Each four-example window must refute every declared competitor; query rotations are supported rather than assumed.

**Evidence:** Focused tests enumerate all 40 relative alignments of the eight-slot lesson schedule and five-step gray anchor in every band. The source-bound census materialized 100 lessons per band, 1,500 distinct grids total, and held out each of five pairs once: 0/300 production ambiguities and 0/1,500 rotated ambiguities.

**Limits:** The census samples the production materializer and finite declared rivals. It does not enumerate every program consistent with the examples.

## D7 — Portable tests and a reusable reproducer

**Choice:** Replace fixed parent-depth canonical paths with `reviewer_support`; add `workspace/shortcut_probe.py` plus compact Racket-bound counterexample files.

**Rationale:** The pre-repair task-test stage stopped before pytest in its copied runtime. The reproducer gives future reviewers one command that checks the strongest shortcut against canonical examples and the exact selected-rule output.

**Evidence:** `checks/task-tests/result.json` reports 16/16 portable tests passing. `checks/shortcut-probe.log` is the successful reproducer output; the prior failed import is retained in the same review history as an implementation iteration.

## D8 / R8 — native parametric depth-placement family

**Parameter.** `depth_policy ∈ {same_depth, reverse_depth}` is fixed for an episode. `same_depth` returns the selected canonical Racket program byte-for-byte. `reverse_depth` keeps divider discovery, source-side detection, colors and copy direction unchanged, but reverses copied depths within the input's observed source span.

**Required sequential dependency.** Step A locates the unique full-height nonzero divider and measures the maximum absolute source-column distance `M`. The input-dependent intermediate is that measured `M`. Step B maps each source depth `d` to target depth `M + 1 - d` on the opposite side. Step B cannot choose its target columns before Step A supplies `M`; substituting `M - 1` changes the protected-Racket result by 30 cells on the retained qualified case.

**Episode assembly.** The adapter supports 2–6 demonstrations and 1–4 queries, with native qualification at three demonstrations and four queries. Four stored queries are structurally distinct (14×17, 18×21, 24×27 and a substantive 30×30 case), and the public projector reveals exactly one query per turn without settings, programs, labels, answers, future inputs or count hints. The first public turn is identical to single-query use.

**Learnability audit.** A task-local executable audit checked both settings, seeds 0 and 17, demonstration counts 2, 3 and 6, four queries per episode, and ten named wrong rules. Across 12 episodes and 48 queries it found no harmful survivor and no input failure. This is finite evidence against the named rivals, not a uniqueness proof.

**Native evidence.** `workspace/parametric/promotion.json`, `workspace/parametric/evidence/manifest.json`, and `workspace/parametric/adapter.py` bind the source. Native qualification passed four jobs (two settings × two seeds), each with three demonstrations and four queries, for 40 protected-Racket pair executions. The protected causal witness is `checks/4e16917b1bde/causal/witness.json`; qualification is `checks/4e16917b1bde/qualification/qualification.json`. Portable task tests pass 27/27.

**Approval boundary.** The family is reviewer-ready only. Exact integrated bytes still require owner qualification and acceptance; neither the variant nor any trajectory is training-admitted by this return.
