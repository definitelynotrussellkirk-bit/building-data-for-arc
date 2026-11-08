# Working notes: 167a1374f6c3

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Baseline measurement

- Baseline generator version `1.3.0`, SHA-256 `6f3f1a6ab3e321c260f8e9d2d66fe14c43580b641d9faa52d6ac276afaabb314`.
- Before battery: 7 green, 2 advisory, 3 failed.
- Blocking defects: missing `RULE_HASH`; dead/overlapping axes; malformed degenerate textures; non-exact overrides; unknown overrides accepted.
- Canonical support defect: a disconnected canonical motif contradicted the connected-only invariant; hard band had zero profile-floor support.
- Semantic defect: no executable witness/rival contract.

## Selected repair

- Preserve the selected Racket authority and pin normalized rule hash `91349b01b34b`.
- Replace the nine-axis baseline declaration with six exact observable axes: height, width, code count, motif color, motif cell count, and motif connectivity.
- Use a transform-sensitive 3–8-cell catalog with connected and disconnected templates and D4 variants.
- Assemble lessons from a three-slot schedule so any three consecutive examples cover all code meanings, repetition, both connectivity classes, and rectangular alignment.
- Shuffle each slot’s lawful code multiset by seed to expose order and improve output diversity without losing coverage.
- Declare executable rivals/witnesses and the canonical-only `deduplicate_codes` shortcut.
- Add a source-bound task-local lesson probe that discovers rival declarations from the selected generator itself.

## Final evidence

- Final generator version `2.0.0`, SHA-256 `2f0de677a7499b6c0f40a6eca80de08a6d1ae83f6495f4e5daa1ea4fcf87cc6c`.
- After battery: 12/12 stages green.
- Focused tests: 18 passed.
- Lesson census: 100/100 identifiable in each band; zero ambiguous survivors; 396–399 unique inputs per 400 generated examples.
- Exact repeated-code counterexample is retained under `checks/shortcut-deduplicate/` and matches Racket authority.
- Selected Racket source and canonical data were not edited.

## Limitations

The default schedule intentionally uses three dimension/cell-count profiles and two- or three-code programs; exact overrides cover the full advertised ranges. The shape family and rival set are finite. Passing the recorded census establishes the stated sampled claims, not universal identifiability against every conceivable rival.
## Current reviewer considerations

Source SHA-256: `2f0de677a7499b6c0f40a6eca80de08a6d1ae83f6495f4e5daa1ea4fcf87cc6c`.

# Decisions: 167a1374f6c3

## Evidence policy and prior work

I treated the pinned packet baseline as the only starting source of truth. I did not apply or copy a prior return. I inspected the retained passing example `b90d4c3d5553` only as an architectural lead for exact axes, an authority mirror, witnesses/rivals, and lesson identifiability; no task-specific geometry, palette, or rule was copied.

The baseline was measured before editing. Its SHA was `6f3f1a6ab3e321c260f8e9d2d66fe14c43580b641d9faa52d6ac276afaabb314`, and its battery result was 7 green, 2 advisory, and 3 failed. This kept inherited claims separate from current measurements.

## D1 — Keep the canonical authority unchanged and pin it

**Choice.** Preserve the selected Racket rule and canonical row unchanged, add `RULE_HASH = "91349b01b34b"`, and implement a small Python authority mirror for tests and semantic probes.

**Rationale.** The rule already reproduced all four canonical pairs and passed Racket smoke/parity. The defects were in the generator’s domain and declarations, not the authority.

**Alternatives rejected.** Editing Racket to fit the baseline generator would have changed a functioning authority without evidence. Treating an archival raw carrier as selected authority was also rejected; the final sync report explicitly identifies that carrier as inactive and divergent.

**Probe.** Exact canonical-pair tests, 120-draw Racket smoke, and authority sync/parity. Evidence: `checks/after/checks/167a1374f6c3_after_rule_smoke.json` and `checks/after/checks/167a1374f6c3_after_authority_sync.json`.

## D2 — Replace nine misleading axes with six exact observable controls

**Choice.** Declare only `grid_h`, `grid_w`, `n_codes`, `motif_color`, `motif_cells`, and `motif_connectivity`.

**Rationale.** Each selected axis maps directly to an observable property and can be honored exactly across the entire stated domain. The baseline’s `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and aliased `texture` either overlapped, were constant/dead, or described malformed examples rather than lawful task variation.

**Alternatives rejected.** Keeping degenerate textures as ordinary axis values was rejected because `no_codes`, `no_motif`, and `code_in_motif_row` violate the task grammar and made multi-axis overrides impossible to interpret. Keeping constant axes for metadata completeness was rejected because it advertises variation that the generator does not provide.

**Failure mode considered.** Cross-product overrides could fail because of placement or output-size constraints. The shape catalog, dimensions, and code limits were chosen so every declared boundary combination is constructible; therefore `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is intentionally empty.

**Probe.** The final override battery exercised 479 cases in three bands and accepted 43,110/43,110 lawful draws, while rejecting an unknown key.

## D3 — Include disconnected motifs

**Choice.** Make connectivity an explicit exact axis with both `connected` and `disconnected` values.

**Rationale.** One canonical example is disconnected. The baseline invariant “connected base motif” therefore excluded valid canonical support and weakened the profile floor.

**Alternative rejected.** Enforcing connected motifs for aesthetic simplicity was rejected because it contradicted canonical evidence. Treating the disconnected example as a one-off exception was rejected because exceptions are harder to test and teach than an honest axis.

**Probe.** All four canonical inputs pass `self_check` and `strict_canonical_like`; each three-example lesson includes both connectivity classes.

## D4 — Use a bounded transform-sensitive shape catalog

**Choice.** Provide connected and disconnected shape templates for every cell count 3–8, choose among all D4 variants, require 2–4 by 2–4 crops, and reject shapes whose transform orbit has fewer than four states.

**Rationale.** A small catalog makes the full override domain auditable, ensures every placement fits grids 7–14 by 10–16, keeps galleries within ARC’s 30×30 limit, and avoids highly symmetric motifs that hide transform meanings.

**Alternatives rejected.** An unconstrained random walk could produce symmetric, thin, oversized, or hard-to-audit shapes. A single fixed motif would satisfy the rule but create a severe memorization shortcut. Expanding beyond 4×4 was unnecessary for this repair and would complicate five-code output bounds.

**Limitation.** The catalog is finite. D4 variants, colors, placement, dimensions, and code order create broad instance variation, but future audits may identify shape-family-specific rivals.

## D5 — Use a three-slot teaching curriculum

**Choice.** Default generation cycles through:

1. a repeated-code, disconnected canonical-size profile;
2. a connected half-turn/CCW expanded profile;
3. a connected flip/CW/CCW canonical-size profile.

Any three consecutive examples are a complete lesson. The start rotates cyclically so all three possible lesson alignments are tested.

**Rationale.** Random independent examples can leave a lesson without a code meaning, repeated code, disconnected motif, or rectangular alignment witness. A short deterministic schedule provides exact coverage while RNG still varies color, shape orientation, placement, and code order.

**Alternative rejected.** Purely random programs were rejected because good marginal witness frequency does not prove each assembled lesson is identifiable. A longer schedule was unnecessary: three slots already cover the known semantic distinctions.

**Probe.** Focused tests check nine cyclic starts in every band. The source-bound census checks 100 lessons per band and reports 300/300 identifiable with zero ambiguous survivors.

## D6 — Shuffle lawful code order within each slot

**Choice.** Seed-dependently shuffle each slot’s multiset while preserving its semantic contents.

**Rationale.** The initial curriculum fixed one program order per slot. It passed semantic gates but compressed the battery’s output diversity to 37%. Shuffling keeps all lesson guarantees while exposing order effects and increased final output diversity to 71%.

**Alternative rejected.** Adding more schedule slots would increase maintenance surface without addressing the underlying order collapse as directly. Fully resampling programs could destroy per-lesson guarantees.

**Probe.** A test first required at least two program orders per slot across 40 seeds while preserving each slot’s multiset. Final diversity: 300 pairs, 100% unique inputs, 71% unique outputs, zero flags.

## D7 — Name and execute plausible rivals

**Choice.** Implement executable rivals for a wrong code map, independent rather than cumulative transforms, omitted initial panel, reversed code order, bottom-aligned panels, and deduplicated codes. Link nine semantic witnesses to those rivals and make `lesson_identifiable` reject any rival that fits all demonstrations but changes the query.

**Rationale.** Text-only claims are easy to drift from code. Executable rivals let tests and the battery verify exact disagreements.

**Canonical shortcut.** `deduplicate_codes` is separately declared in `CANONICAL_SHORTCUTS` because it fits all four canonical pairs. Generated repeated-code demonstrations refute it.

**Limitation.** The competitor set is explicit and finite. Passing it does not prove that no other hypothesis can fit a lesson.

## D8 — Build a source-bound reusable lesson probe

**Choice.** Add `workspace/lesson_probe.py`, importing the exact generator source and iterating the generator’s actual shortcut/competitor declarations.

**Rationale.** The battery’s lesson sample is deliberately small. A task-local tool lets future agents cheaply repeat or extend a 100-lessons-per-band census without stale copied rival names.

**Recorded sampler.** Three consecutive demonstrations followed by one query; cyclic start `lesson_index % 3`; seed `seed_base + band_index*1,000,000 + lesson_index`; all easy/medium/hard bands. The report records source hash, domain limits, disagreements, exceptions, schedule counts, and unique-input/output counts.

**Probe.** A focused regression verifies source binding and declaration discovery. The retained full report is `checks/lesson-probe/167a1374f6c3_lesson_probe.json`.

## D9 — Preserve honest solve boundaries

The blind task was solved before generator inspection. The post-repair episode was prepared from the frozen final generator bytes and solved only from its visible challenge. Because the rule had been seen during repair, earlier exposure is declared `yes`; no Racket source or reference solution was consulted during the solve. The masked queries remain deliberately unscored in this return.

## Final self-review

The repair introduces a structured default distribution: only three default dimension/cell-count profiles and two- or three-code programs, with the full 1–5 code and dimension/cell ranges available through exact overrides. This is deliberate for lesson coverage, but maintainers should not read default marginal diversity as exhaustive domain coverage.

No new canonical-only shortcut was found beyond the explicitly recorded repeated-code deduplication rival. The 300-lesson census refutes every declared rival in every sampled lesson, but it is finite evidence rather than a completeness theorem.
