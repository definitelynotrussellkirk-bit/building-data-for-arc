# Working notes: fa5bb24054bc

## Baseline diagnosis

The selected `2.0.1` sampler used random solid/ring search and only required some nonzero off-diagonal relation. The canonical five pairs contain no equal-area/different-hole comparison, so two strong rivals fit all demonstrations: (1) label every equal-area pair as `6`, and (2) never emit label `2`. Baseline checks also found no pinned `RULE_HASH`, dishonest/dead override metadata, degenerate ordinary textures, zero strict-profile support, and no executable semantic contract. The retained `evidence/associated_notes.jsonl` was empty, so no prior return was used as a lead.

## Repair

- Pinned the unchanged canonical authority with `RULE_HASH = b6e6c6e2c73c` and versioned the sampler as `3.0.0`.
- Replaced rejection-driven random geometry with a bounded constructive catalog whose feature signatures are known by construction and independently rechecked.
- Added a deterministic four-sample teaching cycle: area-only equality, hole-only equality, both equal, and neither equal. `EXAMPLES_NEEDED = 4` matches that curriculum.
- Added canonical-size anchors every seventh sample. Anchor panel order is shuffled so strict-profile support does not collapse output diversity.
- Reduced advertised exact controls to the three observable axes actually supported: `grid_h=3..8`, `n_panels=2..6`, and `sep_width=1..2`. Unknown, wrong-type, and out-of-range overrides are rejected.
- Kept all ordinary panels at most three columns wide, making every legal joint override fit the ARC 30-column limit (observed maximum 28).
- Added independent semantic witnesses and canonical-fitting rivals, strict/canonical profile checks, an independent Python oracle, negative fixtures, and a task-local qualification tool.

## Iterations retained in evidence

1. The first repair failed output-diversity lint because canonical anchors used fixed panel order. Randomizing only anchor order fixed that without changing dimensions or semantic coverage.
2. Anchoring every fifth sample aligned badly with the profile-floor probe and overrepresented one weak pattern. A seven-sample cadence preserves a canonical hit in every eight-sample window while broadening the probe distribution.
3. The first semantic witness declaration mislabeled general observables as rival witnesses. The final contract names only the real equal-area/different-hole counterexample and maps it to both declared rivals.
4. A task-local qualifier initially double-counted canonical profiles; a failing regression test caught it before the tool was retained.

## Final evidence and limits

Final generator SHA-256: `d659db585ae666b9c525b250c09f624da3070624bf9b9c54872e0af366cfbfe3`.

- Full after battery: 12/12 green.
- Selected portable tests: 52/52 pass.
- Production lesson census: 100 lessons per band, 300/300 materialized, 0 ambiguous, 0 hook warnings, 0 scoring errors, 1,498 unique inputs among 1,500 pairs; both canonical-fitting rivals were refuted in every lesson.
- Task-local qualifier: all 64 cyclic starts, all 60 legal joint override combinations, and 300 broad samples pass; both rivals were independently refuted 213 times.

The result is still a finite constructive distribution, not a proof of universal induction. Shapes are drawn from a named width-three catalog with at most three holes, and the four-profile schedule is deterministic in hidden sample index. Colors, D4 orientation, placement, panel count, separators, fillers, and panel order vary, but a learner could still memorize shape prototypes rather than acquire a fully general hole counter. No sample-index metadata is present in puzzle grids.
## Current reviewer considerations

Source SHA-256: `d659db585ae666b9c525b250c09f624da3070624bf9b9c54872e0af366cfbfe3`.

# Decisions for fa5bb24054bc

## D1 — Preserve the canonical rule

**Choice.** Keep the canonical Racket row unchanged and pin `RULE_HASH = b6e6c6e2c73c`.

**Rationale.** Canonical outputs and the independent Python mirror agree; the defect was sampling/teaching, not authority. Rule smoke and authority sync stayed green before and after.

**Alternatives considered.** Rewriting the Racket rule or changing the output encoding. Both would add authority risk without repairing the missing semantic contrast.

**Failure mode / limit.** The generator and semantic hooks must remain bound to this hash. Any future authority edit needs a new review rather than silently inheriting these measurements.

## D2 — Construct feature signatures instead of searching randomly

**Choice.** Build panels from a bounded catalog with known `(area, holes)` signatures, then apply orientation, color, placement, separator, and panel-order variation.

**Rationale.** The baseline only required some relation and could systematically miss area-only equality. Construction makes each required contrast guaranteed, makes override combinations total, and removes rejection/flakiness.

**Rejected alternative.** Keep random polyomino/ring generation and retry until every relation appears. This is slower, harder to prove within width 30, and still allows rare lesson-level omissions.

**Failure mode / limit.** A finite catalog may encourage prototype recognition. D4 variants, fillers, multi-hole pairs, and independent feature checks reduce but do not eliminate that shortcut.

## D3 — Use a four-profile cyclic curriculum

**Choice.** `sample_index % 4` selects `area_only`, `holes_only`, `both`, or `unrelated`; `EXAMPLES_NEEDED = 4`.

**Rationale.** Every four consecutive samples contain labels `0`, `2`, `3`, and `6`. This directly refutes the two strongest canonical-fitting rivals and is cheap to test for every cyclic start.

**Alternatives considered.** Randomly choose profiles per sample, or put all four signatures in every sample. Random choice permits incomplete lessons; forcing four panels everywhere would narrow output dimensions and erase valid 2–3 panel cases.

**Probe.** `workspace/qualify.py` checked starts 0–63, each with all four labels and all four profiles.

**Failure mode / limit.** The hidden schedule is deterministic. It is not visible in grids, but out-of-band sample-index access would reveal it.

## D4 — Anchor canonical profiles every seventh sample

**Choice.** Every seventh sample uses `N=3`, height 3/4, and separator 1/2 to cycle through canonical input profiles; panel order is shuffled.

**Rationale.** Strict-profile support is guaranteed in each eight-draw floor window without dominating the ordinary distribution.

**Rejected alternatives and observed failures.** A fixed anchor order caused low output diversity. A five-sample cadence aligned with the profile-floor probe and overrepresented a weak same-feature pattern. The seven-sample cadence passed both gates.

**Failure mode / limit.** Anchors are deliberately simple and may repeat dimensions; only one seventh of sample indices are anchored, and ordering/colors/orientations vary.

## D5 — Advertise only observable exact controls

**Choice.** Retain only `grid_h=3..8`, `n_panels=2..6`, and `sep_width=1..2`; reject unknown and non-integer controls.

**Rationale.** Baseline metadata included aliases and palette/density controls that were not honored. The final axes map directly to pixels and provenance.

**Alternatives considered.** Keep compatibility aliases or declare textures as helpful. That would preserve misleading surface area and complicate joint-domain testing.

**Probe.** All 60 Cartesian combinations materialize, observe exactly, self-check, and stay within width 28.

**Failure mode / limit.** Difficulty still affects default draws, but an explicit override wins. Shape family and color count are intentionally not public controls.

## D6 — Keep ordinary panel width at most three

**Choice.** Use width-three solids, rings, and ladders; allow up to three holes by height.

**Rationale.** This gives a simple global width bound for six panels and two-column separators: `6×3 + 5×2 = 28`, below ARC's 30-column maximum.

**Alternative.** Wider arbitrary frames. They increase geometric variety but make some legal joint overrides impossible or require an incompatibility table.

**Failure mode / limit.** Width is narrower than the most general task domain. The reported generator claim is therefore bounded, not universal.

## D7 — Name only real semantic witnesses

**Choice.** The executable witness is the exact equal-area/different-hole pair; both declared rivals are mapped to it. Broader observables remain lesson checks, not “witnesses.”

**Rationale.** An intermediate contract treated six ordinary predicates as witnesses without named rivals, which the semantic gate correctly rejected.

**Probe.** The 3×7 witness has features `(8,0)` and `(8,1)`; canonical Racket returns `[[5,2],[2,5]]`, while `same_area_means_both` returns `[[5,6],[6,5]]`.

## D8 — Retain independent reviewer tooling

**Choice.** Add `workspace/reference_probe.py`, `workspace/qualify.py`, and 52 tests under the selected task.

**Rationale.** Production helpers should not verify themselves. The oracle independently splits panels and counts holes; the qualifier reads the generator's actual declared rivals and checks cyclic starts/joint axes.

**Failure mode / limit.** The Python oracle is not authority. Canonical Racket remains the source of labels, and the witness was separately checked through `arcpuzzles apply`.
