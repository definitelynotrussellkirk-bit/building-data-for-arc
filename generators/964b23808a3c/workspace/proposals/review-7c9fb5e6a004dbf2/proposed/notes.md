# Working notes: 964b23808a3c

## 2026-10-05 review `review-feb73249509b92e2`

### Baseline diagnosis

The baseline generator's prose and distribution encoded a different task from
the canonical authority. It described coloring only the gaps between markers
with the previous/upper marker color; the authority colors from row 0 through
each marker with the current/lower marker color. Defaults generated only clean
2–4-column cases where every multi-marker column ended in 5. That omitted the
canonical one-target case, non-target columns, internal-5 traps, and floating
terminators. The baseline `self_check` consequently rejected four of the five
canonical inputs by treating every multi-marker column as a target. It also
lacked `RULE_HASH`, strict exact controls, canonical profile coverage, and an
executable lesson/rival contract.

The before battery retained in `checks/before/` had seven blocking failures:
lint, self-check, defect lint, distribution, profile floor, overrides, and
authority sync.

### Repair decisions

- Kept the canonical Racket rule unchanged and pinned `RULE_HASH` to
  `c7e69da25375`.
- Rebuilt generation around the actual selector: only columns whose last
  nonzero value is 5 are targets.
- Added a four-profile deterministic schedule matching every canonical
  shape/palette profile: minimal, clean, noisy, dense.
- Added mixed distractors, an internal-5 trap, top gaps, and floating terminal
  rows so canonical-fitting shortcuts are contradicted in complete lessons.
- Exposed six exact axes and reject invalid calls rather than coercing them.
- Salted layout RNG by difficulty so bands differ geometrically while retaining
  the same exact profile schedule.
- Added an independent Python rule mirror, canonical acceptance, strict
  validation, override observation, five semantic witnesses, six plausible
  rivals, and a lesson-level identifiability hook.
- Set `EXAMPLES_NEEDED = 3`. Consecutive four-pair windows contain two
  shortcut-refuting examples, so any one-pair query rotation leaves at least
  one such witness in the three demonstrations.
- Synchronized only the selected base solution's `racket_target.target_code`
  text to the exact canonical source. The older archival `raw_code` remains
  untouched; execution parity is retained and the canonical authority was not
  edited.

### Regression and reusable probe

`tests/test_generator.py` covers canonical ownership, the independent oracle,
rule/contract declarations, joint exact overrides, invalid-call rejection,
canonical profile coverage in every band, shortcut fit on canonical labels,
rival refutation, all query rotations in curriculum windows, determinism,
malformed inputs, axis decoupling, and non-dead difficulty bands.

`workspace/review_probe.py` is a source-bound future-review tool. With 16 seeds
and nine cyclic windows per seed/band it observed 715 unique inputs, exact
profile coverage, a counterexample for every declared rival, and zero failures
in 2,304 query rotations. It reads canonical answers and must remain closed
during solve episodes.

### Final measured state

Generator SHA-256:
`c8437cf46718d553fcf6f856c3b0abf428a09e7debf9f370a224f6135d5f52c7`.

- Official after battery: 12/12 stages green (`checks/after/`).
- Selected task tests: 94/94 passed (`checks/task-tests/`).
- Required-rotation semantic gate: 12/12 lessons and 48/48 rotations
  identifiable; 600/600 strict draws (`checks/required-rotations-final/`).
- Production census: 300 lessons, 1,200 pairs, 1,200 rotations, 1,065 unique
  inputs, zero ambiguity or scoring/materialization errors
  (`checks/lesson-census.json`).
- Post-repair visible solve: revision 1 passed 3/3 examples; prior rule exposure
  declared honestly in `solve/summary.json`.

### Limitations

The semantic result is relative to six declared rivals and sampled/generated
inputs; it is not a proof of unique induction against all possible hypotheses.
The fixed four-profile schedule intentionally emphasizes canonical support over
uniform coverage of every legal joint axis combination. Exact override tests
cover legal joint controls separately.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c8437cf46718d553fcf6f856c3b0abf428a09e7debf9f370a224f6135d5f52c7`.

# Decisions for `964b23808a3c`

## D1 — Treat the canonical Racket program as unchanged authority

**Choice.** Pin `RULE_HASH = "c7e69da25375"`, leave the canonical row untouched,
and make the Python generator, summary, mirror, and tests conform to it.

**Rationale.** Canonical outputs consistently implement a coherent rule. The
failure was in generation and description, not in labels. Replacing the rule
would have invalidated valid canonical data and hidden the actual defect.

**Alternative rejected.** Rewrite Racket to match the baseline “previous color
between marks” description. That contradicts all canonical outputs and would be
a task mutation rather than a generator repair.

**Probe.** Canonical ownership tests compare all five labels against an
independent Python oracle; final rule smoke and authority sync are green.

## D2 — Define a target by its last nonzero marker, not by marker count

**Choice.** A target column is exactly a nonempty column whose last nonzero value
is 5. Non-target columns may contain multiple marks and may contain 5 internally.

**Original rationale.** The baseline rationale was not documented beyond its
summary. Its code implicitly assumed all multi-marker columns were targets.

**Rationale.** The selector follows both authority behavior and canonical
counterexamples. It permits lawful distractors without weakening validation.

**Alternatives rejected.** “Every multi-marker column,” “any column containing
5,” and “only bottom-row 5” each fit the narrow baseline but fail on retained
mixed/floating witnesses.

## D3 — Use current/lower-marker segment ownership and preserve the floating tail

**Choice.** Starting at row 0, each marker colors the interval after the previous
marker through its own row. Rows below the last marker remain unchanged.

**Rationale.** This is the smallest direct restatement of observed authority
behavior. Reserving a top gap and, when possible, a blank row before the
terminator makes direction and boundary effects visible instead of vacuous.

**Alternatives rejected.** Previous-marker fill, start-at-first-marker fill, and
extend-terminal-5-to-bottom are retained as executable rivals.

## D4 — Four deterministic canonical-anchor profiles

**Choice.** Cycle by `sample_index mod 4` through:

| Profile | Shape | Palette | Targets × marks | Distractors | Terminator |
| --- | ---: | ---: | ---: | --- | --- |
| minimal | 7×7 | 3 | 1×2 | none | bottom |
| clean | 12×12 | 7 | 2×4 | none | bottom |
| noisy | 13×13 | 9 | 2×3 | mixed | floating |
| dense | 17×17 | 10 | 3×5 | mixed | floating |

**Rationale.** These are the four canonical shape/palette profiles. A fixed
cycle makes profile-floor coverage and complete lesson pedagogy deterministic,
while seeds still vary columns, rows, colors, and distractor placement.

**Alternatives rejected.** Broad independent random draws missed all canonical
profile anchors in the before battery. A schedule with target count tied
monotonically to mark count was also rejected after the first after-run linter
identified the correlation; the final schedule includes repeated target counts
with different mark counts.

**Probe.** The task-local probe observed each profile exactly 48 times in each of
`None`, easy, medium, and hard bands for its 16-seed sample.

## D5 — Six strict, observable axes

**Choice.** Expose `grid_h`, `grid_w`, `n_targets`, `n_marks_per_target`,
`distractor_mode`, and `terminator_position`. Reject unknown keys, wrong types,
out-of-range values, and unsupported difficulty values. Declare no hidden
incompatibility combinations.

**Rationale.** These controls map directly to observable input properties and
the task's branch structure. Exact overrides are more useful for testing and
controlled dataset construction than legacy palette/style aliases whose effect
was indirect or clamped.

**Alternatives rejected.** Silent clipping and permissive aliases make dataset
requests irreproducible and allowed invalid override tests to appear successful.

**Probe.** Joint-override tests compare `observe_overrides` with every requested
value, and the official override matrix is green.

## D6 — Mixed distractors are curriculum witnesses, not arbitrary noise

**Choice.** Every mixed profile contains (1) a column with an internal 5 whose
last marker is not 5 and (2) a separate multi-marker column with no 5. Remaining
texture realizes the exact profile palette/density without modifying targets.

**Rationale.** These two structures separately refute “any 5” and “all
multi-marker columns.” They are lawful under the authority and visually simple
enough for a 9B model to learn from three demonstrations.

**Alternative rejected.** Random singleton clutter could increase diversity but
would not reliably distinguish a selector rule. Pure clean columns caused the
baseline teaching defect.

## D7 — Floating terminators in both shortcut-refuting profiles

**Choice.** Noisy and dense targets end at `height - 2`; the final row remains
untouched. Minimal and clean terminate at the bottom.

**Rationale.** Seeing both cases refutes both “bottom-row 5 is required” and
“always extend 5 to the bottom.” Two floating examples per four-pair window mean
one remains a demonstration even when the other is the query.

**Alternative rejected.** Probabilistic floating endpoints could yield complete
lessons with no boundary witness.

## D8 — Three demonstrations, one query, rotations supported

**Choice.** Keep `EXAMPLES_NEEDED = 3` and assemble consecutive four-profile
windows. Declare six competitors and reject a lesson when one fits all demos but
changes the query.

**Rationale.** Three demonstrations are sufficient because each four-pair
window has two mixed/floating profiles and all four expose top-gap and
current-marker direction. The schedule supports downstream query rotation,
which was verified rather than assumed.

**Alternatives rejected.** Two demonstrations can lose both mixed witnesses
under rotation. Ordered-query-only support would be cheaper, but downstream
assembly permits rotations and a full rotation pass was affordable.

**Probes.** Required semantic gate: 48/48 rotations. Production census:
1,200/1,200 rotations. Exhaustive local windows: 2,304/2,304 rotations.

## D9 — Difficulty changes geometry, not semantic profile

**Choice.** Salt layout, palette, row, and distractor RNG labels by difficulty,
while retaining the same profile cycle and contract in every band.

**Rationale.** The first repair reused identical geometry across bands because
the underlying RNG labels did not include difficulty. Band-specific geometry
adds real variation without making hard examples semantically different or
breaking canonical profile coverage.

**Alternative rejected.** Difficulty-specific profile omission would make some
bands miss canonical anchors and curriculum witnesses.

## D10 — Validation accepts the authority domain, not only defaults

**Choice.** `self_check` validates rectangular 0..9 grids, requires at least one
lawful target with at least two marks and a non-5 mark, and rejects no-op target
sets. It does not require the default number of targets, exact profile shape, or
absence/presence of distractors.

**Rationale.** Validators should own canonical and override-generated inputs,
not encode one sampler's defaults. `strict_canonical_like` intentionally aliases
this task-lawful validator, yielding a measured strict rate of 1.0.

**Limitation.** This is a task-domain validator, not a proof that every accepted
input is pedagogically rich. Witness and lesson checks provide that second
layer.

## D11 — Selected authority text synchronization only

**Choice.** Replace only the bound base solution's selected
`racket_target.target_code` with the exact canonical source text. Retain the
older equivalent `raw_code` archive.

**Rationale.** The authority-sync gate requires selected exact identity and
separately tolerates labelled archival divergence when execution parity holds.
This preserves provenance while removing ambiguity about which source is active.

**Alternative rejected.** Editing or deleting archival raw text would erase
useful lineage; changing canonical source was unnecessary.

## D12 — Retain failures and add a reusable probe

**Choice.** Keep the before battery and the first after battery. Add
`workspace/review_probe.py` rather than relying only on one-off shell snippets.

**Rationale.** The intermediate run caught two real quality problems—axis
correlation and dead difficulty bands—after semantic correctness was already
green. The reusable probe gives future agents one command for canonical parity,
profile coverage, rival refutation, and all cyclic query positions.

**Limitations.** The probe checks six declared rivals, 16 seeds, nine windows per
seed/band, and overlapping windows. It does not enumerate all programs or all
legal inputs; its 715 unique-input denominator is reported explicitly.

## Review `review-7c9fb5e6a004dbf2` — strict entry contract and parametric prototype

### D13 — Strict public scalar contract

The pinned `3.0.1` baseline passed every battery stage except defect lint, which
reported 33 strict-scalar warnings: bool/float/string seeds and sample indices,
plus `sample_index=-1`, were accepted. The negative index reached Python profile
lookup and selected the final schedule profile. Version `3.0.2` now validates
both public entry paths before profile or RNG logic, requires exact built-in
integers, rejects negative indices, and removes `int(...)` coercion. Eleven new
parameterized cases exercise both `generate` and `schedule_profile`.

Final generator SHA-256:
`c586f09adde529195a8467eb499005004a68546e46a4b10b3e80617f02d431e5`.
The final battery is 12/12 green and the portable task suite is 111/111 green.
The Racket authority and `RULE_HASH = c7e69da25375` are unchanged.

### D14 — Proposed selector × segment-owner family

A runnable, non-production prototype lives in `workspace/parametric/`. It varies
`selector_mode` (`ends_in_5` / `contains_5`) and `segment_mode` (`current` /
`previous`) while preserving the original vertical marker/fill reasoning. The
canonical default is byte-for-byte the selected Racket program. A setting is
chosen once per episode and held fixed across three demonstrations and one
query. Seed-17 evidence executes all labels in Racket; every episode's demos
refute the three alternative settings and every query independently separates
them. This is bounded authoring evidence only, not training or API approval.

### D15 — Final lesson evidence

The final-source census used 100 lessons per band and hold-one-out query
rotation. It materialized 300 lessons, 1,200 pairs, 1,200 rotations, and 1,062
exact unique inputs with zero ambiguity, materialization errors, hook warnings,
or scoring errors against the declared rivals. The result is finite-rival
coverage, not proof against arbitrary programs.
