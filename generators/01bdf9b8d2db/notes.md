# Working notes: 01bdf9b8d2db

## 2026-10-03 review repair

- Kept the selected Racket authority unchanged and pinned its canonical hash
  `816bf3c1378a` in the generator.
- Removed ordinary/advertised negative textures (`missing_marker`,
  `conflicting_markers`, `no_chambers`, and unmarked chambers). They contradicted
  the task's lawful teaching contract and produced override/self-check failures.
  Such cases may still be useful as separate validator tests, but are not normal
  generated lessons.
- Restricted public dimensions to the canonical envelope and schedules abstract
  canonical profiles rather than copying coordinates.
- Divider placement is constructive and spacing-safe. All advertised override
  combinations are exact, observable, and accepted; unknown/non-integer axes are
  rejected loudly.
- Every connected chamber receives exactly one seed. Seed colors may repeat, as
  required by the canonical 9-chamber/7-color example.
- Every three consecutive sample indexes contain a gapped example. A divider gap
  merges nominal rectangles and refutes the strongest canonical-fitting rival:
  filling each rectangle independently.
- Added task-local contract tests and `workspace/lesson_probe.py`. The final probe
  checks 100 complete lessons per band, 1,200 unique generated inputs, all five
  canonical pairs, declared rivals/witnesses, and optional selected-Racket parity.

## Retained limitations

- The semantic claim is limited to the declared `independent_rectangles` rival
  and the generator's lawful manifold; it is not a universal induction claim.
- The generator does not emit malformed walls, missing/conflicting seeds, or
  other negative validator fixtures as ordinary lessons.
- Passing checks do not admit the generator to training; approval remains a
  separate catalog decision.

See root `REVIEW.md`, `DECISIONS.md`, and `checks/lesson_probe_final.json` in the
review return for measurements and reproduction commands. Imported associated
notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `281c46cb5254cf1051dd9d25a8e693481d1a58b7d9a23645428040c1d9d943c5`.

# Design decisions for `01bdf9b8d2db`

## D1 — Pin the existing authority; do not rewrite it

**Input and original rationale.** The selected canonical Racket program already
matched all canonical outputs and the before battery's authority-sync and rule
smoke stages passed. The baseline generator nevertheless omitted `RULE_HASH`.
The provenance of that omission is unknown.

**Decision.** Add `RULE_HASH = "816bf3c1378a"`, keep the canonical and task-local
rule bytes unchanged, and test all five canonical pairs with an independent
Python flood fill.

**Rejected alternatives.** Rewriting the Racket program would add semantic risk
without evidence of an authority defect. Computing a hash dynamically would not
provide the static source pin required by lint/intake.

**Probe and failure mode.** `checks/before/...before_lint.log` reproduces the
missing pin. The after rule-smoke, Racket-lint, and authority-sync stages are
green. A future authority change must update the pin only after explicit source
synchronization and parity checks.

## D2 — Remove negative textures from ordinary generation

**Input and original rationale.** The baseline comments presented
`missing_marker`, `conflicting_markers`, `no_chambers`, and unmarked chambers as
rule-hiding/negative variety. Their deeper historical rationale is unknown. In
practice they shared the public `texture` axis with normal lessons while
`self_check` rejected important combinations, producing contradictory contracts
and thousands of override findings.

**Decision.** Ordinary generation now emits only lawful teaching inputs: every
4-connected non-wall chamber has exactly one seed. Missing/conflicting-marker
cases remain represented as explicit validator regression mutations in the test
suite, not as normal lessons.

**Rejected alternatives.** Keeping a public mixed positive/negative texture axis
would make accepted generation depend on implicit purpose. Silently weakening
`self_check` would admit lessons with ambiguous or different semantics. A future
separate negative-fixture API could be justified, but was unnecessary here.

**Probe and failure mode.** Baseline defect/override evidence is under
`checks/before/checks/`; focused rejection tests are in
`tests/test_generator.py`. The limitation is explicit: ordinary sampling does not
exercise malformed inputs.

## D3 — Use abstract canonical profiles inside the canonical envelope

**Input and original rationale.** Canonical inputs occupy five height/width/color
profiles, including a 9-by-13 board with nine chambers but only seven seed colors.
The baseline used much broader, difficulty-narrowed dimensions and globally
distinct marker colors; the before profile floor was advisory. The original
broad-range rationale appears to have been generic visual variety, but exact
provenance is unknown.

**Decision.** Define five abstract profiles `(height, width, vertical dividers,
horizontal dividers, target distinct seed colors)` and schedule them by difficulty.
Coordinates and seed locations remain randomized. Public dimensions are 7–10 by
10–13. Repeated colors are deliberate when chamber count exceeds the profile's
target distinct count.

**Rejected alternatives.** Copying canonical coordinates would overfit. Keeping
4–10 by 6–16 would spend probability mass outside canonical morphology and make
exact overrides band-dependent. Forcing globally distinct seeds contradicts the
canonical repeated-color case.

**Probe and failure mode.** Final profile floor reports 13/20, 11/20, and 18/20
exact hits in easy/medium/hard. Focused tests require dense support and the exact
nine-chamber/seven-color profile. The profiles are a curriculum prior, not a
claim that all lawful boards must have those shapes.

## D4 — Make every advertised override constructive, exact, and observable

**Input and original rationale.** The baseline declared axes wider than its
per-band draw ranges, selected dividers with fragile sampling, sometimes lacked
enough realizable gap cells, accepted unknown keys, and had no observer. The
baseline report's top root causes were band-dependent `grid_h`/`grid_w` rejection
and texture/self-check conflicts.

**Decision.** Use spacing-safe enumeration for exact divider counts, carve gaps
only from non-intersection divider cells, reject unknown and non-integer values,
and expose `observe_overrides(grid)` for all five public axes. The advertised
Cartesian domain has no incompatible combinations.

**Rejected alternatives.** Declaring hundreds of incompatibilities would preserve
a misleading API. Retry-until-valid generation would obscure provenance and
could still fail. Letting difficulty narrow explicit overrides violates the exact
control contract.

**Probe and failure mode.** `checks/after/...after_override_results.json` is PASS
with no findings/warnings and unknown-key verdict `rejected`. Tests exercise lower,
upper, and mixed values under every difficulty. Any future axis must gain both a
constructive implementation and an observer before being advertised.

## D5 — Validate connected chambers, not nominal rectangles

**Input and original rationale.** The authority operates on 4-connectivity through
non-5 cells. Divider gaps can therefore merge nominal rectangular compartments.
The baseline validator and generation paths allowed missing or conflicting
markers, which made the intended chamber rule unclear.

**Decision.** `self_check` now verifies rectangular ARC grids, canonical-envelope
size, complete color-5 border, spaced divider geometry, no stray walls, 0–2
observable gaps, and exactly one seed in every connected chamber.

**Rejected alternatives.** Validating per rectangle would encode the strongest
wrong rival. Allowing zero seeds would rely on authority behavior not represented
by canonical teaching examples; allowing multiple seeds leaves color choice
order-dependent.

**Probe and failure mode.** All five canonical inputs and 600/600 semantic-census
draws pass strict validation. Explicit tests mutate a lawful grid to missing and
conflicting seed cases and require rejection.

## D6 — Schedule a decisive connectivity witness in every three-demo lesson

**Input and original rationale.** All five canonical pairs are also solved by the
plausible shortcut “treat divider lines as unbroken and flood each rectangular
compartment independently.” Random gaps alone do not guarantee that each complete
lesson refutes it.

**Decision.** `schedule_profile` makes sample indexes congruent to 1 modulo 3
gapped. Therefore every three consecutive demonstration indexes contain a
decisive witness. `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`,
`SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, and
`lesson_identifiable` declare and test the relationship explicitly.

**Rejected alternatives.** Merely increasing average gap probability can still
produce all-plain lessons. Making every board gapped removes useful ordinary
coverage and shifts the distribution. A coordinate-specific witness would be
brittle.

**Probe and failure mode.** The final 100-lessons-per-band probe found 133 gapped
inputs among 400 per band and 100/100 lessons per band refuting the rival. This
supports only the declared rival; future rivals need their own witnesses and
lesson-level analysis.

## D7 — Add focused tests before implementation and retain the red run

**Decision.** Add task-local tests for authority binding, canonical acceptance,
exact overrides, invalid inputs, determinism/global-RNG isolation, lesson
scheduling, profile density, repeated colors, exact gap counts, and validator
mutations.

**Evidence.** `checks/tdd_red.log` records 23 failures against the baseline and
`checks/task_local_tests_final.log` records 32 passes against the final source.
The root repository fixture was not edited.

## D8 — Build a source-bound probe future agents can rerun

**Decision.** Add `workspace/lesson_probe.py` rather than relying on an ad hoc
notebook. It imports the final generator by path, reads current declarations,
uses pinned lesson seeds, records exact denominators and source hashes, checks an
independent Python oracle, and optionally executes the selected Racket authority
without fallback.

**Rejected alternatives.** Copying rival names or profile assumptions into a
one-off report would drift from source. The built-in 12-lesson semantic check is
a smoke test, not the required large lesson audit when a canonical-fitting rival
exists.

**Probe and limitation.** `checks/lesson_probe_final.json` covers 300 complete
lessons and 1,200 unique inputs. It makes no universal induction claim and should
be rerun after any profile, schedule, rival, witness, or authority change.

## 2026-10-24 native parametric admission candidate

- Preserved the approved production generator byte-for-byte at SHA-256
  `281c46cb5254cf1051dd9d25a8e693481d1a58b7d9a23645428040c1d9d943c5`.
- Added a native episode-fixed `finish` family under `workspace/parametric/`:
  `fill_all` returns the exact canonical Racket program bytes, while
  `mark_smallest_total` first performs the canonical chamber flood, computes
  flooded cell totals per seed color, selects the least-total color (lowest
  color on a tie), and recolors that entire flooded class to 9.
- The adapter supports 2–6 demonstrations, exactly four distinct sequentially
  revealed queries, matched inputs across settings, and a substantive 30x30
  query. Hidden settings, programs, seeds, and answers remain outside the public
  projection.
- The bounded teaching audit covered 18 jobs (seeds 0/17/97, demonstration
  counts 2/3/6, both settings), executed 132 protected-Racket labels, and
  defeated five executable selector rivals plus two Python structural rivals.
  This is finite evidence, not a universal uniqueness claim.
- Native qualification passed four fresh jobs (both settings x seeds 0/17),
  with 32 protected-Racket evaluations. The source-bound inventory contains 19
  declared files; qualification and execution receipts are retained under
  `checks/01bdf9b8d2db/qualification/`.
- Sequential dependency: A floods each input-derived chamber; the intermediate
  is the histogram of flooded cell totals by color; B uses that histogram to
  choose the class recolored to 9. The protected counterfactual counts input
  seeds instead of flooded area, chooses color 1 instead of 8, and changes 13
  final cells. The replay is retained at
  `checks/01bdf9b8d2db/sequential-witness.json`.
- Reviewer state is `ready`, not accepted. Owner source integration, native
  acceptance, and any training admission remain pending.
