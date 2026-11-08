# Working notes: adcdcbe48f64

## Intended rule and authority

For input `g` of height `h` and width `w`, return an `h × 5w` grid whose five
horizontal tiles are `g | mirror_lr(g) | g | mirror_lr(g) | g`. The canonical
Racket authority was not changed. `RULE_HASH` remains `5ed1759c50b3`.

Current generator version: `3.3.0`.
Final generator SHA-256:
`b20458ed1a1bf323d5d543d9f9f1a4eda1aa6112182e2b83ed0b3488954539bb`.

## Input grammar and exact controls

- Public exact axes: `grid_h=4..15`, `grid_w=4..6`, `palette_size=2..4`.
- Every advertised cross-product is constructive in every difficulty band.
- Inputs use nonzero colors only, each color appears at least three times, no
  color exceeds 70% of the tile, and every tile is visibly LR-asymmetric.
- Difficulty changes sampling bias only. Legal values are exactly `None`,
  `easy`, `medium`, and `hard`; invalid scalars are rejected.
- Private texture modes vary local statistics but are not public axes because
  they are not uniquely recoverable from returned pixels.

## Current lesson schedule

All labeled canonical pairs are width four, so `fixed_width_4` is a real
canonical-fitting shortcut. It is executable in `LESSON_COMPETITORS`, while the
legacy semantic registry remains exactly the visible-reflection witness plus the
`plain_repeat` and `mirror_first` rivals required by the frozen task contract.

`LESSON_SCHEDULE_PERIOD = 3`:

- sample indices congruent to 0 mod 3 default to canonical 4×4 with palette 2/3;
- the other two residues default to width 5/6;
- explicit `grid_h`, `grid_w`, and `palette_size` overrides always take
  precedence and retain the full advertised domain.

This schedule was added after an intermediate 300-lesson census found 16
production ambiguities and 58/1,200 query-rotation ambiguities against the width
shortcut. Every four consecutive samples now contain at least two non-width-four
examples, so any one held-out query leaves a width witness among three demos.

## Verification and limits

Final evidence:

- `checks/after/checks/adcdcbe48f64_after_battery_summary.json`: 12/12 green,
  rotations required, all three schedule residues enumerated.
- `checks/task-tests-final2/result.json`: 90/90 portable task tests.
- `checks/lesson-census-final.summary.json`: 300 production lessons and 1,200
  query rotations, zero ambiguity/errors, 1,145 unique inputs.
- `checks/tdd/all-focused-final2.log`: 90/90 direct focused tests.

Finite checks cover the declared fixed-width, plain-repeat, and mirror-first
competitors plus bounded generic candidates; they do not prove universal
identifiability. The default schedule correlates width class with sample index,
but the transformation is identical at every residue and explicit exact controls
remain unrestricted.

## Proposed parametric extension

`workspace/parametric/tile_count.py` is an isolated prototype with episode-level
`tile_count ∈ {3,5}`. Five is the exact canonical default; three preserves the
same alternating original/mirror composition with a shorter output. Both exact
Racket programs execute, every retained demo distinguishes the settings, and the
canonical setting passes 10/10 canonical parity checks. This prototype does not
change production generation, approval, or training admission.
## Current reviewer considerations

Source SHA-256: `b20458ed1a1bf323d5d543d9f9f1a4eda1aa6112182e2b83ed0b3488954539bb`.

# Decisions for `adcdcbe48f64`

## D1 — Preserve the canonical authority

**Choice.** Keep the Racket rule and rule hash `5ed1759c50b3` unchanged.

**Rationale.** Rule smoke, independent Python parity, canonical examples, and authority sync all showed that the selected behavior is already correct: alternate original and left-right mirror five times, beginning with the original.

**Alternatives considered.** Change the number/order of tiles in production, add width-specific branches, or modify canonical labels. All would change the task rather than repair its generator and were rejected.

**Probe and failure mode.** The final battery’s rule smoke, Racket lint, and authority-sync stages pass. This protects the selected authority bytes but does not prove the prose explanation spans every rule-applicable input.

## D2 — Validate difficulty before constructing the generation context

**Choice.** Accept only `None`, `"easy"`, `"medium"`, and `"hard"`, with booleans and numeric aliases rejected.

**Rationale.** The baseline `defect_lint` showed invalid values reached generation instead of failing at the public boundary. Silent coercion makes replay and band analysis unreliable.

**Alternatives considered.** Treat unknown values as medium/default or accept integer aliases. Both hide caller defects and make source-bound receipts ambiguous.

**Probe and failure mode.** Nine invalid scalar/container cases fail in a focused regression; every legal value is exercised by the existing task suite. Future difficulty names require an intentional contract change and new tests.

## D3 — Model fixed width four as a lesson competitor, not a false semantic rival

**Choice.** Keep the exact legacy `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, and `WITNESS_RIVALS` registry, while declaring `fixed_width_4` in `LESSON_COMPETITORS` and testing its canonical fit explicitly.

**Rationale.** `plain_repeat` and `mirror_first` do not fit canonical examples, so labeling either as a canonical shortcut was factually wrong. The real shortcut is width four: it fits all ten canonical pair occurrences and fails on lawful width-five/six inputs. The frozen selected-task fixture also consumes the exact semantic registry as a compatibility surface.

**Alternatives considered.** Add `fixed_width_4` to `CANONICAL_SHORTCUTS` and widen `SEMANTIC_RIVALS`; replace a legacy rival; or weaken the fixture. The first caused an integration failure because the shared semantic gate and exact fixture imposed incompatible surfaces; the other two would alter inherited API/tests outside the allowed repair scope.

**Probe and failure mode.** Canonical fit, wide-input disagreement, lesson rejection, and registry compatibility are all focused tests. The competitor covers the observed canonical-size shortcut, not every possible size-conditional program.

## D4 — Use a deterministic three-slot curriculum schedule

**Choice.** Every third default sample is canonical 4×4; the other two default samples have width 5 or 6. Height and palette retain their bounded grammar, and explicit public overrides always win.

**Rationale.** Random weighting produced a measurable teaching defect: 16/300 production lessons and 58/1,200 query rotations left the width-four rule alive. With three demonstrations plus one query, a period-three schedule guarantees at least two variable-width samples in every four-sample window, so any held-out pair leaves at least one width witness among the demonstrations.

**Alternatives considered.**

1. **Resample whole lessons until a width witness appears.** Rejected because the generator API emits one input at a time and hidden rejection loops complicate deterministic replay.
2. **Increase demonstrations.** Rejected because the assignment’s lesson contract is three demonstrations and one query; more examples increase cost without repairing the sampler itself.
3. **Randomly force one wide sample per four draws.** Rejected because independent calls cannot reliably coordinate that state.
4. **Make every sample width 5/6.** Rejected because it would erase canonical 4×4 profile support.

**Probe and failure mode.** The final battery exhaustively covers all three residues at seed 0 in every band and all four query positions; the 300-lesson census covers broader fixed recipes. A downstream assembler that ignores accepted sample order or mixes unrelated starts must rerun its own identifiability gate.

## D5 — Keep the schedule observable but out of the public axis contract

**Choice.** `grid_h`, `grid_w`, and `palette_size` remain the only public exact axes. The schedule is a curriculum policy, not a new override.

**Rationale.** The emitted grid itself reveals all three exact axes through `observe_overrides`. Exposing a `schedule_slot` override would leak an internal teaching mechanism and create redundant ways to request width/shape.

**Alternatives considered.** Add `canonical_slot`/`profile` as public axes or infer slot from the returned grid. The former is unneeded; the latter is already possible from dimensions but does not uniquely encode generation history.

**Probe and failure mode.** Exact override tests show every advertised value and cross-product still works in every band. Default marginal widths are intentionally correlated with sample index; consumers requiring IID dimensions should not assume them.

## D6 — Parameterize output tile count only in an isolated prototype

**Choice.** Propose episode-level `tile_count ∈ {3,5}`, with five canonical and three alternative. Choose once from the episode seed and hold it fixed across all three demonstrations and the query.

**Rationale.** Count changes the executed transformation while preserving object role, LR reflection, alternating composition, starting orientation, and input grammar. Every pair visibly distinguishes settings by output width.

**Alternatives considered.** Start with mirror, switch to vertical reflection, recolor tiles, or vary input sizes. Starting orientation/axis changes more of the spatial rule; recoloring adds unrelated semantics; input size is not a rule parameter.

**Probe and failure mode.** Both exact Racket programs execute, Python parity holds, the five-tile setting matches all ten canonical occurrences, and two complete deterministic episodes reject the alternative setting. The evidence is finite and does not establish solver benefit or justify production integration.

## D7 — Retain failures while keeping the return within evidence budget

**Choice.** Preserve compact source-bound summaries, exact counterexamples, red tests, final receipts, and one full final lesson census; omit redundant multi-megabyte row-level intermediate reports after recording their hashes and compact witnesses.

**Rationale.** The return budget is 25 MiB expanded. Keeping three near-duplicate 7–16 MiB census bodies would crowd out more useful exact regression and replay evidence.

**Alternatives considered.** Delete all failures or retain every full census. The first would make the repair unauditable; the second would make packaging fail.

**Probe and failure mode.** Compact summaries retain source hashes, counts, recipes, first witnesses, and exact reproducer paths. The omitted bodies cannot be inspected row-by-row from this return, but their decisive counterexamples and hashes are retained.

## D8 — Self-review the new curriculum restriction

The repair narrows default width by schedule residue, so I treated “sample index predicts width class” as a new possible shortcut. That cue does not predict the output transformation: the same alternating rule applies to every residue, and all legal dimensions remain available through explicit controls. Final diversity/profile/override gates, all-residue rotation enumeration, and the 300-lesson census found no declared-rival teaching failure.
