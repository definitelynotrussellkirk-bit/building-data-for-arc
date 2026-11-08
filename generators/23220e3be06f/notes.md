# Working notes: 23220e3be06f

## Starting point

The selected baseline was generator version `2.1.1`, SHA-256 `f3e7d870609fcf9a497d0633fbe18a448c84920c72923f980cf0037d02710e2d`. No prior return or populated associated-note record was present for this task, so the canonical examples, selected Racket authority, baseline generator, and fresh before-battery were the primary evidence.

The before battery failed five blocking stages (`lint`, `selfcheck`, `defect_lint`, `dist_gate`, and `override`) and left `profile_floor` and `semantic_gate` advisory. The retained summary is `checks/before/checks/23220e3be06f_before_battery_summary.json`.

Root causes were:

- no canonical `RULE_HASH` pin;
- an acceptance-only `self_check` that did not reject rule-irrelevant mutations;
- monochrome five-cell motifs although every canonical motif uses two colors;
- an advertised four-color profile that ordinary generation could not reach;
- dead or overlapping texture controls and exact overrides that were ignored;
- no strict canonical-profile contract, executable semantic rival, or lesson-identifiability contract;
- a command schedule that could leave the only flip example as the held-out query.

## Repair

Version `3.1.0` pins `RULE_HASH = "710976311dfe"` and leaves the selected Racket rule and canonical rows unchanged.

The ordinary sampler now generates exactly one interior motif with 4–8 occupied cells in exactly two colors. Both support and colored pattern are required to be fully asymmetric under all eight D4 transforms. This makes every one of the six authority commands observable and prevents accidental transform aliases. Motifs may have 2–3 four-connected components, matching the fragmented morphology present in the canonical examples.

The profile schedule contains all five exact canonical `(height, width, palette-size)` triples in every difficulty band, plus nearby legal profiles. It supports two meaningful palette modes: `overlap` (one motif color equals the command color, yielding canonical palette size 3) and `distinct` (canonical palette size 4). The only advertised axes are real exact controls: `grid_h`, `grid_w`, `code`, `n_cells`, and `palette_mode`; unknown or invalid overrides raise, and the full Cartesian product is supported.

`self_check` now validates the command grammar, motif size, exact two-color requirement, placement, connectivity envelope, and D4 asymmetry. `strict_canonical_like`, `observe_overrides`, and `reference_output` make profile and override checks executable. The declared `rotations_only` rival fits all usable canonical examples but disagrees on commands 5 and 6; witnesses, canonical shortcuts, lesson competitors, and `lesson_identifiable` explicitly test that distinction.

The first repaired schedule (version `3.0.0`, SHA `e1b571de51519dda046b2b4f662b4f933c1680b1dd5e9f920f3e8890760d3c0b`) passed ordinary production-order lessons but failed a stronger rotated-query census: 75 of 1,200 held-out rotations were ambiguous and 675 rotation warnings were recorded. That evidence is retained in `checks/lesson-census-v3.0.json`. Version `3.1.0` changes the default four-pair command sequence to paired `A,B,A,B`, using a stable mixed-seed residue so counter-like seeds cannot alias the schedule. Every permitted holdout therefore retains another demonstration of its command.

## Test-driven evidence

The task-local suite was written before implementation and observed failing. Retained RED/GREEN logs include:

- `checks/tdd-red-clean.log`: 40 expected failures against the baseline behavior;
- `checks/tdd-green-attempt1.log` and `checks/tdd-green-attempt2.log`: implementation and parity-harness corrections;
- `checks/tdd-rotation-red.log`: four failures exposing the held-out-query schedule defect;
- `checks/tdd-rotation-green.log`: a second failure exposing seed/counter residue aliasing;
- `checks/tdd-rotation-green2.log`: 46 passing tests after the mixed-residue schedule.

The independent probe at `workspace/reference_probe.py` deliberately uses SHA-derived seeds rather than sequential seed/sample pairs. On final source SHA `659095ddc5c43b0205f72a425150b1dc77ef7bc4ff26460485f8e57be1890a98`, it measured 360/360 distinct generated inputs, all six commands in every band, 225/360 exact canonical-profile hits, 360/360 fully asymmetric motifs, zero self-check failures, zero nondeterministic replays, 5/5 canonical Python-mirror matches, and 64/64 Racket parity matches (`checks/reference-probe.json`).

## Final verification

- Official after battery: all 12 stages green, no advisory or pending stages (`checks/after/checks/23220e3be06f_after_battery_summary.json`).
- Source-bound selected task tests: 46 passed (`checks/task-tests/`).
- Production lesson census: 300 lessons (100 per band), 1,200 unique inputs, 0 production ambiguities, 0 warnings, 0/1,200 rotated-query ambiguities, and 0 rotated warnings (`checks/lesson-census.json`).
- Exposed post-repair visible solve: 3/3 visible examples pass and is hash-bound to the final generator. Earlier rule exposure is disclosed; no reference was consulted during that solve (`solve/summary.json`).

## Limits and self-review

The finite rival census establishes separation only for declared plausible rivals, not universal rule induction. The motif domain intentionally excludes one-color, transform-symmetric, empty, and border-colliding cases because they weaken command observability or the canonical grammar. The repair introduces no new authority behavior: all labels remain generated by the unchanged Racket rule.

A final shortcut review checked whether the paired schedule could be defeated by holding out any one of the four materialized pairs. It could not for the declared canonical-fitting `rotations_only` rival: all 1,200 rotated holdouts were non-ambiguous. The independent probe also confirmed that both palette modes, every command, and all canonical profiles remain reachable, so the schedule repair did not collapse distribution support.
## Current reviewer considerations

Source SHA-256: `659095ddc5c43b0205f72a425150b1dc77ef7bc4ff26460485f8e57be1890a98`.

# Design decisions for 23220e3be06f

## D1 — Preserve the selected Racket authority

**Decision.** Keep the canonical rule unchanged and pin its current hash `710976311dfe`.

**Rationale.** The authority correctly implements all six commands and matches all five canonical pairs. The failures were in sampling, validation, controls, and teaching support—not labels.

**Rejected alternative.** Narrowing the authority to rotations would match the most obvious canonical subset but would discard commands 5–6 encoded by the selected rule and preserve the strongest canonical shortcut.

**Probe.** Official `authority_sync`, `racket_lint`, and `rule_smoke` are green; the independent probe has 64/64 Racket parity matches.

## D2 — Match canonical scale and palette without copying five examples

**Decision.** Schedule every exact canonical `(height, width, palette-size)` profile in every band, then add three nearby profiles. Use meaningful `overlap` and `distinct` palette modes.

**Rationale.** The baseline's claimed palette-size-four support was unreachable and its monochrome motifs did not resemble any canonical motif. Exact profile support protects fidelity while nearby profiles retain generalization.

**Rejected alternatives.** Replaying a fixed motif bank would overfit morphology; unconstrained random sizes failed the profile floor. A third arbitrary color mode was rejected because it had no canonical or semantic role.

**Failure mode/limit.** This is profile coverage, not a proof that all higher-order canonical morphology is matched. `checks/reference-probe.json` records 225 exact profile hits among 360 draws and the full observed profile set.

## D3 — Require two-color, fully asymmetric motifs

**Decision.** Generate 4–8 occupied cells in exactly two colors and reject any support/color pattern with a nontrivial D4 symmetry.

**Rationale.** Every command must cause an observable, uniquely attributable output. Color-aware asymmetry prevents a support shape that looks asymmetric geometrically from still aliasing transforms after coloring.

**Rejected alternatives.** Monochrome five-cell polyominoes were the baseline defect. Allowing symmetric motifs and relying on resampling at lesson assembly would save generator effort but make exact overrides unreliable and validators weaker.

**Failure mode/limit.** Symmetric, one-color, empty, and malformed cases are intentionally outside ordinary training; this narrows edge-case robustness in exchange for identifiable lessons.

## D4 — Advertise only real exact controls

**Decision.** Keep five axes: `grid_h`, `grid_w`, `code`, `n_cells`, and `palette_mode`; validate unknown/invalid values and support their full Cartesian product.

**Rationale.** The baseline had dead/overlapping textures and ignored overrides. Exact observable controls make distribution experiments and the override matrix trustworthy.

**Rejected alternative.** Retaining compatibility aliases for old texture names would preserve an API that had no stable observable meaning. They were removed rather than silently mapped.

**Probe.** `observe_overrides` round-trips every advertised axis; the final official override stage is green and task tests enumerate joint support.

## D5 — Use paired command scheduling, not one-of-each novelty

**Decision.** A default four-pair lesson follows `A,B,A,B`, where the seed selects adjacent commands modulo six through a mixed residue.

**Rationale.** Production lessons use three demonstrations and one query. Duplicating both commands means every legal held-out pair still has a same-command demonstration. The mixed seed finalizer avoids an observed alias between sequential seeds and sequential sample indices.

**Rejected alternatives.** The first repair scheduled broader command novelty, but a rotated-query census found 75/1,200 ambiguous holdouts. A fixed global pair would teach too little command diversity; the seed rotates pairs across all six commands.

**Probe.** TDD logs preserve both failures. Final census: 0/300 production ambiguities and 0/1,200 rotated ambiguities.

## D6 — Declare the strongest plausible canonical shortcut

**Decision.** Implement `rotations_only` as `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with flip-command witnesses and lesson validation.

**Rationale.** The rival fits every usable canonical example but gives a different answer for commands 5 or 6. It is therefore a realistic model shortcut, not a synthetic straw man.

**Rejected alternative.** Merely counting all six command values across a large sample does not ensure any complete lesson distinguishes the rival.

**Failure mode/limit.** Passing one finite declared-rival set does not prove unique induction against every possible program. Reports state this explicitly.

## D7 — Build reusable independent evidence

**Decision.** Add 46 source-bound tests and `workspace/reference_probe.py`, using SHA-derived seeds and optional Racket parity.

**Rationale.** Sequential seed/sample pairs initially produced a misleading residue pattern. A deliberately independent sampler catches schedule aliasing and gives future agents a fast way to reproduce canonical/profile/parity claims.

**Rejected alternative.** Depending only on the shared battery would leave task-specific rotated-holdout and exact morphology checks implicit.

## D8 — Final self-review

The final source was checked for a new schedule shortcut by rotating all 1,200 materialized pairs through the query position; none remained ambiguous for the declared rival. Distribution collapse was checked independently: all six commands, both palette modes, all exact canonical profiles, and 360 distinct/asymmetric inputs were observed. The principal remaining limitation is conceptual rather than a known defect: undeclared rivals and out-of-domain malformed inputs were not exhaustively enumerated.
