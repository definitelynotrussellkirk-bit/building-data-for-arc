# Working notes: a36fd3a00941

## Final repair (generator 3.0.0)

The Racket authority was not changed. The generator is pinned to authority
`RULE_HASH = d0dcd1dd1256` and implements the same rule in a Python mirror:
extract each non-zero 4-connected monochrome component, crop to its bounding
box, sort by `(2 * (height + width), left, top)`, and pack the crops
left-to-right, top-aligned, with one zero column between crops.

The imported 2.0.0 sampler drifted away from the canonical task. It drew
11–14 by 14–18 scenes with solid blocks/rings/double rings, advertised axes
that did not round-trip, mixed invalid negative fixtures into its ordinary
texture domain, and did not bind the rule hash. More importantly, the
canonical demonstrations admit two strong shortcuts—ascending bounding-box
area and ascending occupied-cell count—and the old distribution did not make
those rivals a required teaching contrast.

Version 3.0.0 uses only the four observed canonical input profiles:
`8x12`, `9x11`, `8x13`, and `9x12`. Every ordinary sample contains exactly
three objects with this intended-order signature:

| Intended order | bbox | perimeter | bbox area | occupied cells |
|---|---:|---:|---:|---:|
| small | 2x2 | 8 | 4 | 4 |
| middle | 3x2 | 10 | 6 | 5 |
| large | 1x5 | 12 | 5 | 5 |

Thus the intended perimeter order is `small, middle, large`, while both area
and occupied-count ordering put `large` before `middle`. The large object is
also placed before and left of the middle object, colors are deliberately out
of semantic order, one crop is sparse, and the crops have unequal heights.
Those choices jointly refute the declared area, count, scan-order, color,
descending-perimeter, solid-bbox, bottom-alignment, and no-gap rivals.

The only public override is `scene_profile`; it round-trips exactly and unknown
axes fail closed. Difficulty changes deterministic nuisance placement only, so
all bands preserve the same semantic counterexample while producing different
realized grids. Three demonstrations are required and every generated example
independently refutes every declared rival.

## Rejected intermediate design

An initial repair used bboxes `2x2`, `3x4`, and `2x6`. It did separate
perimeter from area/count, but produced a 3x14 output that was wider than some
canonical inputs and made the task a reshape rather than the canonical shrink.
It also left the difficulty bands byte-identical. The retained failure reports
under `checks/after-lint/` and `checks/after-defect_lint/` motivated the final
`2x2`, `3x2`, `1x5` construction and deterministic band layouts.

## Verification and retained probes

- Task-local regression suite: 20/20 passed on the final generator before the
  portable import-only tightening; the final fresh-copy replay records the
  definitive count.
- Full after battery: 12/12 green.
- Required-rotation semantic smoke: 12/12 lessons and 48/48 query rotations,
  with zero ambiguity or errors.
- Large census: 300 materialized lessons, 1,200 pairs and 1,200 query
  rotations, zero ambiguity/materialization/scoring errors, 1,035 unique
  inputs.
- `workspace/probe_shortcuts.py` recomputes canonical shortcut fit from the
  checked-out canonical ledger and emits a generated counterexample plus every
  declared competitor output.
- `counterexamples/area-count-shortcut-seed123.json` retains the exact
  source-bound witness checked against the Racket authority.

## Known limits

The generated grammar is intentionally narrow: it teaches the decisive rule
on canonical-scale scenes rather than attempting broad shape coverage. It does
not generate equal-perimeter ties, so the left/top tie-break remains authority
and mirror behavior rather than a learned contrast. Identifiability is only
against the eight explicitly declared rivals; the census is not a proof against
all possible hypotheses.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b4346a02502a9be2f1b7a4293918fa94698ebd3246e6588bfe8c92812a3665a5`.

# Decisions for `a36fd3a00941`

## D1 — Preserve and pin the existing authority

**Choice.** Keep the Racket rule unchanged and set `RULE_HASH = "d0dcd1dd1256"`. The Python `rule_mirror` is a test/lesson oracle only; the selected Racket rule remains authoritative.

**Why.** Canonical outputs already agree with the perimeter-sort/crop/pack rule. The defect was the generator distribution and contract, not the transformation. `checks/after/checks/a36fd3a00941_after_battery_summary.json` reports selected-source synchronization and execution parity `PASS`.

**Alternative rejected.** Editing canonical data or the Racket source would have changed the task to fit the sampler and expanded the review scope without evidence that the rule was wrong.

**Failure mode/limit.** An archival raw-code copy remains textually divergent, but the selected authority is synchronized and execution parity passes; this is reported rather than “fixed” outside the selected task.

## D2 — Match the canonical input envelope exactly

**Choice.** Cycle deterministically through `8x12`, `9x11`, `8x13`, and `9x12`, the four observed canonical profiles. Expose only `scene_profile` as an override.

**Why.** The imported sampler used roughly `11–14 x 14–18` scenes and failed the exact and envelope profile floor. Exact profile scheduling removes accidental size/area cues and makes every advertised profile observable and testable.

**Alternatives considered.** A broader rectangular envelope could preserve more visual variety, but it would reintroduce a distribution gap that had no task evidence. Random selection was also unnecessary; a period-four schedule gives deterministic coverage in every short window.

**Probe/evidence.** R1 in `REVIEW.md`; `checks/before-profile_floor/`; final profile floor in `checks/after/`; test `test_every_scene_profile_override_round_trips_exactly`.

**Failure mode/limit.** Dimension variety is intentionally only canonical variety. It is not evidence that the rule generalizes to arbitrary ARC sizes.

## D3 — Use a minimal exact counterexample signature

**Choice.** Generate objects with bbox/perimeter/area/count tuples:

- `2x2 / 8 / 4 / 4`
- `3x2 / 10 / 6 / 5`
- `1x5 / 12 / 5 / 5`

The intended perimeter order is therefore small–middle–large, while ascending bbox area and occupied count both place the line before the middle object.

**Why.** Bbox-area and occupied-count sorting each fit all `4/4` labeled canonical pairs. They are the strongest simple rivals because they use the same extracted objects and only replace the sort key. The signature separates both on every ordinary sample rather than depending on rare seeds.

**Rejected intermediate.** The first repair used `2x2`, `3x4`, and `2x6`. It separated the keys but produced width-14 outputs and changed a canonical shrink into a reshape for width-11/12 inputs. `checks/red-tight-profile/` records the new failing assertion; the final construction always packs to `3x11`.

**Probe/evidence.** `workspace/probe_shortcuts.py`; `counterexamples/area-count-shortcut-seed123.json`; R2/R4 in `REVIEW.md`.

**Failure mode/limit.** The grammar teaches perimeter ordering strongly but does not cover every possible component morphology.

## D4 — Make all declared rivals lose in every example

**Choice.** Besides area/count, place the large line first in row-major order and left of the middle object, permute colors away from semantic order, keep the middle crop sparse, use unequal crop heights, top-align the intended output, and retain one-column gaps.

**Why.** A three-demo lesson should not depend on a lucky seed or sample position. Each input independently refutes input scan order, color order, perimeter descending, solid bbox replacement, bottom alignment, and gap omission.

**Alternative rejected.** Merely declaring rivals and relying on the lesson assembler to search for a refuting window would be more brittle and would make query rotations vulnerable.

**Probe/evidence.** `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and task-local tests; `checks/required-rotations/`; `checks/lesson-census.json`.

**Failure mode/limit.** These are a finite hypothesis set, not a universal proof of identifiability.

## D5 — Keep difficulty semantic-neutral but observably different

**Choice.** Difficulty controls deterministic nuisance placement only:
`easy=(top0, large-left0, small-left0)`, `medium=(top1, large-left0, small-left1)`, and `hard=(top0, large-left1, small-left1)`.

**Why.** The first implementation accepted difficulty but yielded byte-identical scenes for the same seed/index, making the axis dead. The final layouts guarantee distinct realized grids while preserving the same rule witness and canonical profile.

**Alternative rejected.** Difficulty-specific object signatures would confound difficulty with the teaching rule and complicate lesson comparisons.

**Probe/evidence.** `checks/after-defect_lint/` for the intermediate defect and `test_difficulty_bands_change_the_realized_scene_for_same_seed_and_index` for the final contract.

**Failure mode/limit.** Difficulty does not represent increasing semantic difficulty; it is nuisance variation only and is documented as such.

## D6 — Remove unsupported axes and fail closed

**Choice.** Delete the old grid-size, palette, component-count, density, position, and texture claims. Keep only `scene_profile`; validate it explicitly; reject unknown keys; implement `observe_overrides` for exact round-trip checking. Helpful and degenerate texture lists are empty because no texture contract is needed.

**Why.** The old metadata advertised values the generator either ignored or rejected, and its ordinary texture domain contained negative fixtures. A smaller truthful contract is safer than a broad fictional one.

**Alternative rejected.** Repairing every old axis would add complexity unrelated to the task rule and leave many combinations difficult to guarantee at canonical scale.

**Probe/evidence.** R3 in `REVIEW.md`; baseline override/defect reports; final override and grammar stages.

**Failure mode/limit.** Consumers wanting arbitrary dimensions must use a different generator version rather than an undocumented override.

## D7 — Require three demonstrations and rotation-safe lessons

**Choice.** Set `EXAMPLES_NEEDED = 3`, require a declared rival contract, and implement `lesson_identifiable` over the materialized demos and query. Treat every pair as a possible held-out query in the rotation check.

**Why.** Three demonstrations match the solve/export policy and provide redundant teaching even though each final example already contains the decisive witness. Rotation testing ensures the lesson is not identifiable only because a particular witness was fixed in the query or demo slot.

**Alternative rejected.** One demo would be logically sufficient for the declared rivals but would narrow visual coverage and diverge from the expected lesson format. Ordered-only evaluation would leave a query-position shortcut untested.

**Probe/evidence.** Required smoke: `12` lessons/`48` rotations. Larger required census: `300` lessons/`1,200` rotations. Both have zero ambiguity/errors.

**Failure mode/limit.** Rotations reuse each materialized four-pair bundle; they do not enumerate every possible cyclic window or undeclared rival.

## D8 — Add strict canonical validation and deterministic replay

**Choice.** `self_check` validates the semantic object structure; `strict_canonical_like` enforces the canonical profile and teaching signature. Generation uses task-local `gen_ctx` streams, returns fresh grids, and does not touch global `random` state.

**Why.** Structural validity alone would allow the generator to drift back toward oversized or shortcut-friendly scenes. Strict validation makes the intended distribution executable rather than prose-only.

**Alternative rejected.** Snapshot-only tests would catch a few seeds but not establish the invariant across bands/profiles.

**Probe/evidence.** Forty draws per band in the focused suite, full battery, and the 300-lesson census.

**Failure mode/limit.** Strictness intentionally prevents broader shapes; any future expansion should add a new measured profile rather than silently weakening the validator.

## D9 — Retain a reusable source-bound shortcut probe

**Choice.** Add `workspace/probe_shortcuts.py`, which discovers the packet root portably, reads actual canonical pairs, iterates the generator's current `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and emits source/rule hashes plus all predictions.

**Why.** Future reviewers can re-evaluate shortcut fit after code or canonical changes without copying rival names or trusting stale prose.

**Alternative rejected.** A one-off notebook or hard-coded JSON witness would not detect declaration drift.

**Probe/evidence.** `checks/counterexample-a36fd3a00941/probe.json` and the retained task-local counterexample.

**Failure mode/limit.** The Python mirror is independently compared with a supported Racket `apply` result for the retained witness; the probe alone is not authority.

## D10 — Final acceptance through clean patch replay

**Choice.** Generate the exact six-path delta, extract the original packet afresh, initialize Git at that extraction root, run `git apply --check`, apply, confirm the generator hash, and run the focused tests there.

**Why.** This catches hidden parent-worktree behavior, missing new files, and path assumptions that in-place tests cannot expose.

**Probe/evidence.** `checks/fresh-replay/source.patch`, `checks/fresh-replay/replay.log`, and `checks/fresh-replay/result.json`.

**Failure mode/limit.** The replay tests the selected delta and task suite; the full repository-wide test universe was not run. The task's full 12-stage battery was run separately on identical generator bytes.
