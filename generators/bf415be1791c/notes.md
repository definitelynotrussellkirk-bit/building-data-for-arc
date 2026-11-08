# Working notes: bf415be1791c

Verification basis: repair accepted against the exact source and rule pins. Battery, census, audit and solve results below are reviewer-reported unless an owner rerun is explicitly named. `checks/...` and `solve/...` citations name the original transport paths; retained evidence is indexed in `evidence/review_index.json` and the task-local counterexample/solve directories.

Owner rebase check: 108 focused tests passed locally with `PYTHONPATH=shared/runtime:src`; see `evidence/rebase-check.json`. The broader battery and searched-family results remain reviewer-reported.

## Current design (v2.2.0)

The selected Racket authority is unchanged and pinned as `RULE_HASH = 7d82bc36a98b`. A full-height gray (5) column is the mirror axis. Every magenta (6) source cell lies left of it and has an in-bounds blank reflected destination; the output copies cyan (8) into every such destination while preserving source cells, divider, background, and unrelated distractors.

The imported v1.1.1 generator had dead/ignored controls, a weak validator, and no rule pin. Version 2.0.0 repaired that API but still tested only its declared rival set. Independent second-pass analysis showed that component-size/rank selectors could fit all canonical examples, survive some three-demo windows, and change the query answer.

Version 2.2.0 retains seven exact visible axes: `grid_h`, `grid_w`, `divider_col`, `n_magenta`, `n_components`, `n_distractor_cells`, and `n_distractor_colors`. Every advertised cross-product is constructible and recoverable from the returned grid; unknown, retired, non-integer, Boolean, and out-of-range controls fail loudly.

## Teaching schedule

Canonical magenta component sizes are 4, 4, 5, 5, and 6. The finite eight-profile schedule alternates:

- witness profiles with three components of sizes 7, 2, and 1;
- canonical-scale profiles with ordinary totals and one/two components.

Every four-pair lesson window contains two witnesses, so one remains among the three demonstrations after any cyclic query holdout. A 7/2/1 input simultaneously refutes lower-size thresholds, upper-size thresholds, canonical size ranges, and one/two-component rank selectors. A protected left-side non-magenta distractor refutes “reflect every colored left cell”; preserved source magenta refutes “move rather than copy.”

All three difficulty bands keep the same semantic schedule but vary keyed layout and palette placement. This avoids byte-identical bands without weakening the holdout guarantee.

## Independent shortcut search

`workspace/probe_shortcuts.py` checks the declared contract against canonical pairs and all fixed schedule/query rotations.

`workspace/probe_component_selectors.py` independently derives connected components and searches 104 bounded hypotheses: size thresholds, contiguous size ranges, spatial/size ranks, and total/component-count gates. Fifty fit all canonical pairs. Exact replay on v2.0.0 found 216 ambiguity events across 22 candidates and 72 rotations; v2.2.0 has zero across 96 rotations. Candidates with zero disagreement on generated support are reported as support-equivalent, not falsely “refuted.”

## Validation and limits

`self_check` diagnoses malformed/ragged/non-integer grids without throwing, enforces one full-height divider and no stray gray, bans cyan input, requires left-side magenta and blank in-bounds destinations, and requires unrelated distractors. `observe_overrides` recovers every public control. `strict_canonical_like` accepts all canonical pairs and the declared bounded extension.

The Python mirror is a test oracle only. The decisive 7/2/1 input is bound to the selected Racket authority under `counterexamples/component-selection/`.

The checks are finite. They cover declared rivals, a bounded 104-candidate family, 300 random lessons, every fixed schedule start in three bands, and every cyclic query position; they do not prove unique induction against arbitrary programs or set catalog/training policy.

## Final evidence

- Generator SHA-256: `d89b99051a5ca53548cdb0de9a9685d95b469d8648a4f8f5761eb3c8804be9ae`.
- Focused tests: 108 passed.
- Full after battery: 12/12 green.
- Random census: 300 lessons, 1,200 rotations, zero ambiguity/errors.
- Fixed schedule: 24 lessons, 96 rotations, zero ambiguity/errors.
- Independent family probe: 104 candidates, 50 canonical-fitting, zero final ambiguity.
- Exact Racket-bound witness: `counterexamples/component-selection/`.
## Current reviewer considerations

Source SHA-256: `d89b99051a5ca53548cdb0de9a9685d95b469d8648a4f8f5761eb3c8804be9ae`.

# Decisions for bf415be1791c

## D1 — Keep the selected Racket authority unchanged

**Evidence:** All five canonical labels and the selected Racket program implement the same operation: reflect every magenta (6) source cell across the full-height gray (5) divider and paint only the destination cyan (8), preserving all original cells.

**Choice:** Keep the Racket file byte-identical and pin `RULE_HASH = "7d82bc36a98b"` in the generator.

**Rejected alternative:** Editing the reference rule to match a convenient generator restriction. The observed defect was in sampling and lesson construction, not the authority.

## D2 — Treat the completed v2.0.0 return as a new baseline to adversarially review

**Evidence:** Its declared-rival gates were green, but they could only test hypotheses already listed by the generator. An independent scanner replayed against the exact v2.0.0 patch found 104 selector candidates, 50 fitting every canonical pair, with 216 held-out ambiguity events across 22 candidates and 72 cyclic rotations.

**Choice:** Preserve the old patch and result metadata under `checks/prior-v2.0.0/`, retain complete before evidence under `checks/second-pass/`, and repair the newly measured lesson defect rather than restating the prior return.

**Rejected alternative:** Accepting the previous green census as proof of teachability. A declared-rival pass cannot detect an omitted rival.

## D3 — Keep exact observable controls instead of restoring broad textures

**Choice:** Retain the seven v2.0.0 public axes: grid height/width, divider column, total magenta cells, magenta component count, distractor-cell count, and distractor-color count. Values are strictly typed, range checked, constructively realized, and recoverable from the returned grid.

**Why:** These controls are visible and useful for coverage. The imported broad textures and semantic-sounding knobs were dead, overlapping, or not recoverable.

**Rejected alternative:** Reintroducing texture aliases to preserve the old surface. Silent aliases would recreate the original contract defect.

## D4 — Use one mixed 7/2/1 witness to defeat both lower and upper component filters

**Evidence:** Canonical component sizes are 4, 4, 5, 5, and 6. The v2.0.0 schedule generated no component above 6, making `size_at_most_6` behaviorally identical over its support, while smaller-component filters such as `size_at_least_2` and `size_at_least_3` survived some three-demo windows.

**Choice:** Every witness profile has component sizes exactly 7, 2, and 1. This single construction makes lower thresholds omit the singleton, upper thresholds omit the seven-cell component, canonical 4–6 ranges omit all three, and rank selectors omit one or more components.

**Rejected alternatives:**

- Adding only a singleton fixes lower thresholds but leaves the upper-bound shortcut untouched.
- Adding only an oversized component fixes the upper bound but leaves small-component filters untouched.
- Growing the rival list without changing support would report more names while leaving them observationally equivalent.

## D5 — Alternate witness and canonical-scale profiles in an eight-step schedule

**Choice:** Use the pattern `W,N,W,N,W,N,W,N`, where every `W` has 7/2/1 components and `N` profiles preserve canonical-scale totals and one-/two-component cases. `LESSON_SCHEDULE_PERIOD` is 8 and `EXAMPLES_NEEDED` is 3.

**Guarantee:** Every four-pair lesson window contains two witnesses. Under any cyclic query holdout, at least one remains in the three demonstrations. This is checked for all eight starts and all three difficulty bands.

**Rejected alternatives:**

- One witness per four-pair window: the witness itself can become the query, leaving all demonstrations shortcut-compatible.
- All witness profiles: that would introduce a new distribution shortcut, “every problem has 7/2/1 components,” and lose canonical-scale coverage.
- Randomly hoping for witnesses: it gives no finite holdout guarantee.

## D6 — Search a bounded rival family independently of declarations

**Choice:** Add `workspace/probe_component_selectors.py`, which derives components directly from input grids and enumerates 104 hypotheses spanning size thresholds, size intervals, spatial/size ranks, and total/component-count gates. It does not import the generator's rival registry.

**Why:** Independence catches omissions in `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`. It also reports disagreement counts separately, so a rule that never differs on generated support is labeled support-equivalent rather than “refuted.”

**Limit:** This is a bounded family search, not arbitrary program synthesis. Expanding the family remains future work when new shortcut classes are suspected.

## D7 — Keep declared rivals as an executable lesson contract

**Choice:** Add the most interpretable canonical-fitting filters (`largest only`, size at least 2/3/4, size at most 6) to both the canonical shortcut and lesson competitor contracts, while retaining reflect-all-colors and move-instead-of-copy competitors.

**Why:** The shared semantic gate can provide fast regressions and human-readable diagnoses. The independent family scanner complements rather than replaces it.

**Rejected alternative:** Relying only on the 104-candidate scanner. Shared tooling and solve generation consume declared rivals, so the task must expose both a compact contract and a broader audit tool.

## D8 — Bind the decisive witness to the selected authority

**Choice:** Retain the exact production input, declared-shortcut probe, selected Racket output, and binding verification under `counterexamples/component-selection/`. The verification requires matching final generator SHA, executed/catalog rule hash, input bytes, valid output, Python-oracle agreement, and zero schedule ambiguities.

**Why:** A Python-only counterexample could accidentally encode the same mistaken assumption as the generator. The Racket receipt makes the authority boundary explicit.

## D9 — Preserve exact public domains and deterministic difficulty behavior

**Choice:** Keep `n_magenta=4..10` and `n_components=1..3`; the 7/2/1 witness totals 10 and therefore does not expand the advertised domain. Difficulty affects keyed layout/palette choices but not the semantic schedule residue. Draws remain deterministic and return fresh rows.

**Rejected alternative:** Expanding totals merely to create an oversized component. Seven is already oversized relative to canonical examples and fits the existing total-10 domain.

## D10 — Require four complementary lesson checks

**Choice:** Report all of the following:

1. shared semantic battery with required rotation identifiability;
2. a 300-lesson random census with all four cyclic query positions;
3. exhaustive fixed-period enumeration of 8 starts × 3 bands;
4. the independent component-selector family scan over the same cyclic policy.

**Why:** Random sampling does not exhaust schedule residues, fixed enumeration does not cover random layout support, and declared-rival gates do not discover omitted hypotheses. Their overlap provides stronger finite evidence without claiming universality.

## D11 — Keep infrastructure interruptions honest

**Evidence:** Two foreground parents lost their execution window while the battery was being orchestrated. The documented exact-source resume completed all 12 stages; the final summary records zero failed, interrupted, running, or pending stages, and each stage's own timeout flag is false.

**Choice:** Retain the resume console/progress evidence and report the distinction between parent interruption and stage outcome. Do not rewrite the earlier invocation as a successful synchronous run.

## D12 — Leave audit targets unmodified

**Choice:** Preserve the reproduced `e1e0e42362aa` control-contract defects and `e2266501046d` scalar-type gap in `AUDIT.md` and `checks/audit/`. No audit target source is included in the patch.

## D13 — Recommend routine technical acceptance, not policy approval

The final source has 108 passing focused tests, a green 12-stage battery, zero ambiguity across 300 random lessons/1,200 rotations, zero ambiguity across 24 fixed-schedule lessons/96 rotations, and zero ambiguity for 50 canonical-fitting candidates across the 96 fixed rotations. The authority is unchanged and the exact final patch is replayed in a fresh extraction.

This supports **Acceptance: routine** for the task-local repair. It does not set `approved`, `catalog_approved`, `train_safety`, or claim unique induction against arbitrary programs.
