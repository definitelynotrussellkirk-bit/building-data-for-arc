# Working notes: 6058ff1ae20c

## Baseline finding

Imported `1.2.0` randomly generated one or two isolated marks but advertised several dead or unprobeable axes, omitted `RULE_HASH`, accepted unknown overrides, and had no executable semantic contract. A deterministic 120-lessons-per-band census found canonical-fitting wrong rules surviving complete demo windows in 9 easy, 10 medium, and 11 hard lessons.

## Selected repair

Version `2.0.0` exposes only `grid_h`, `grid_w`, and `scene_profile`. A three-slot schedule cycles `single`, `same_color_pair`, and `ordered_distinct_pair`, guaranteeing that each three-demo lesson refutes `first_seed_only`, `reverse_seed_order`, and `reuse_first_seed_color`. Exact overrides round-trip through `observe_overrides`; invalid and unknown inputs fail closed.

`rule_mirror` is bound to the canonical authority by canonical-pair tests and the full battery. `workspace/lesson_probe.py` performs the larger source-bound census and discovers rivals from the generator declarations.

## Deliberate limits

The reviewed curriculum remains a strict subset of the oracle domain: one/two seeds only, pairs in distinct rows and columns, and colors 2–9. Shared rows/columns, color 1, and three-plus-seed scenes need separate profiles and rivals before inclusion. The Racket rule was not edited.
## Current reviewer considerations

Source SHA-256: `c55525ec48e85e39fa339ec08e3bd174c9123af2748ad3f3b435b072fa9b90ff`.

# Decisions: 6058ff1ae20c

## D1 — Keep the canonical authority unchanged

**Choice.** Pin `RULE_HASH = "95d2eeca4e5d"` and repair only the Python curriculum.

**Original rationale.** The baseline omitted a pin; no rationale was recorded. Direct canonical-pair and rule-smoke checks showed the Racket rule itself was coherent.

**Alternatives considered.** Rewriting the rule to special-case one/two isolated seeds would make the authority match the narrow generator, but would discard lawful behavior already encoded by the canonical fold. Rejected.

**Probe/failure mode.** Final rule-smoke and authority-sync stages pass without a canonical diff. A future canonical rule edit must intentionally update the pin and rerun all semantic witnesses.

## D2 — Replace decorative axes with three exact controls

**Choice.** Keep only `grid_h`, `grid_w`, and `scene_profile` in `AXES`; make every control observable and reject unknown keys.

**Original rationale.** The imported source described eight combinatorial axes, but most were not used by generation or had nonnumeric `varied` ranges. The exact intended semantics of `anchor_corner`, `asymmetry_force`, `position_bias`, and the palette metadata were unknown.

**Alternatives considered.** Implement every old axis. Rejected because several do not teach the rule and would enlarge the override matrix without resolving lesson ambiguity. Marking them diagnostic was also rejected because users could still mistake them for curriculum controls.

**Probe/failure mode.** Boundary round-trip tests cover all exact controls in easy/medium/hard. Unknown keys and wrong types fail closed. Adding a future axis requires an observer and a regression proving that changing it changes the realized input.

## D3 — Use three semantic scene profiles

**Choice.** Generate `single`, `same_color_pair`, and `ordered_distinct_pair` scenes.

**Original rationale.** The old source randomly chose one or two seeds, with no lesson-level plan. Canonical examples contain only singles, leaving multi-seed composition and order unidentified.

**Alternatives considered.** Two profiles (`single`, arbitrary pair) were insufficient because same-color pairs cannot demonstrate overwrite color and distinct pairs alone do not cleanly isolate composition. Three-plus-seed profiles would broaden the rule domain but increase interaction complexity before the basic rivals were controlled. Deferred.

**Probe/failure mode.** The declared rivals are `first_seed_only`, `reverse_seed_order`, and `reuse_first_seed_color`. Canonical tests prove each rival fits every canonical pair; generated witnesses prove the scheduled profiles refute them.

## D4 — Schedule profiles deterministically in every three-demo window

**Choice.** Map `sample_index % 3` to the three profiles and set `EXAMPLES_NEEDED = 3`.

**Original rationale.** None was recorded for the baseline's independent random draws. The baseline census found unidentifiable complete lessons despite adequate marginal two-seed frequency.

**Alternatives considered.** Weighted random sampling was rejected because marginal coverage does not guarantee episode coverage. Rejection sampling per episode would require generator state or an external lesson assembler. A deterministic local schedule is simpler and testable.

**Probe/failure mode.** All cyclic starts are tested. The limitation is predictable profile order; however, the order reveals no output cell values and each input already reveals its own profile. If downstream lesson assembly shuffles or skips indices, it should either preserve consecutive windows or run the lesson gate.

## D5 — Preserve exact canonical shape support

**Choice.** Default `single` scenes choose among `(6,7)`, `(7,7)`, `(5,8)`, and `(8,8)`, the canonical input shapes. Pair scenes use difficulty-aware dimensions from 5 through 12; exact overrides remain available throughout that range.

**Original rationale.** The old default dimensions only covered narrower bands and did not explicitly guarantee canonical support.

**Alternatives considered.** Sample all dimensions uniformly for every profile. Rejected because the profile-floor gate specifically values canonical-size anchors. Fixing every scene to canonical shapes was rejected because it would reduce geometric diversity.

**Probe/failure mode.** Profile-floor and selected-task tests verify canonical support in each band. The 120-lesson census records observed ranges rather than claiming every legal dimension appears in every finite sample.

## D6 — Keep seeds in distinct rows and columns

**Choice.** One or two nonzero seeds; pairs always occupy distinct rows and columns.

**Original rationale.** This invariant existed in the baseline and isolates the row-major intersection behavior.

**Alternatives considered.** Shared-row/shared-column and crowded scenes are lawful under the oracle, but they introduce overwritten seed sites and additional ambiguity about whether original or evolving cells are scanned. Deferred until a separate profile and rivals can test those semantics explicitly.

**Probe/failure mode.** `self_check` rejects shared rows/columns and 3+ seeds. This is a deliberate curriculum boundary, not a statement about the full oracle domain.

## D7 — Use nonzero colors 2–9

**Choice.** Continue excluding color 1 and choose 2–9; distinct-pair scenes sample two different colors.

**Original rationale.** The baseline treated 1 as reserved, but no task-specific reason was documented.

**Alternatives considered.** Include 1 because the canonical oracle accepts any nonzero ARC color. Deferred to avoid changing two dimensions of the curriculum simultaneously; it is listed as a remaining restriction.

**Probe/failure mode.** All cell values are validated as integer ARC colors. A future color-1 expansion should add explicit samples and rerun the rule mirror and lesson rivals.

## D8 — Add an independent mirror and executable semantic contract

**Choice.** Implement `rule_mirror`, `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, witnesses, and `lesson_identifiable`.

**Original rationale.** The baseline had only a structural `self_check`, which cannot detect a curriculum that teaches the wrong generalization.

**Alternatives considered.** Racket-call every sampled lesson. Rejected as unnecessarily expensive after one-time rule-smoke/authority binding; the pure-Python mirror supports large deterministic censuses.

**Probe/failure mode.** Canonical-pair tests ensure every claimed shortcut really is canonical-fitting. Battery semantic/rule stages protect against mirror drift. Any future rival must be discovered from the declarations rather than copied into the probe.

## D9 — Build a source-bound 120-lessons-per-band census

**Choice.** Add `workspace/lesson_probe.py` with deterministic seeds, complete three-demo-plus-query windows, source hashing, unique-input counts, profile counts, domain limits, and rival survival statistics.

**Original rationale.** The built-in small semantic sample is a smoke test, not a lesson-distribution audit.

**Alternatives considered.** Model-based evaluation was rejected as expensive and noisy for this deterministic contract question. A handful of hand-picked witnesses was rejected because it cannot estimate how often lesson assembly misses them.

**Probe/failure mode.** The probe refuses fewer than 100 lessons per band and records the actual sampler. It tests declared rivals only; unknown shortcuts still require reviewer imagination or a broader synthesized rival library.
