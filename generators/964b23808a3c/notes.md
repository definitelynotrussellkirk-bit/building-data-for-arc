# Working notes: 964b23808a3c

## 2026-10-21 review `review-9b20131ac104eca3`

### Current repair

The pinned `3.0.1` source accepted nonliteral scalar lookalikes for `seed` and
`sample_index`, and accepted negative sample indices. The official before battery
was 11/12 green; `defect_lint` emitted 33 strict-scalar warnings. Validation now
requires literal integer seeds and literal nonnegative integer sample indices in
both `generate` and `schedule_profile`. Lawful negative integer seeds remain valid.
The minimal fixture is `counterexamples/strict_scalar_contract.json`, covered by
`tests/test_review_20261021.py`.

The canonical rule and labels did not change: `RULE_HASH` remains
`c7e69da25375`, canonical source SHA-256 remains
`2c8f8aa67ae8104f49348542b8fc365527f316c292c87dd8a6c08a0dfd9cc1a0`, and
execution parity passed. `VERSION` remains `3.0.1` because it salts lawful draws;
a source-bound comparison found 0 differences in 1,728 lawful baseline/final calls.

### Measured final state

Final generator SHA-256:
`1157d7044a6f0ec62be9d5eb4138058fa5ad77448c8f2adbe02bfd8c70d04e20`.

- Final battery: 12/12 stages green.
- Portable selected task tests: 135/135 passed.
- Focused repair plus prototype tests: 41/41 passed.
- Lesson census: 300 lessons, 1,200 pairs and 1,200 query rotations; zero
  ambiguity/errors across 1,065 unique inputs. Episodes use three demonstrations
  and one query.
- Source-bound probe: 2,304 rotations across 715 unique inputs; zero failures
  against the declared rival set.

### Parametric proposal and limits

`workspace/parametric/` contains an unapproved episode-level
`segment_owner={lower,upper}` prototype. `lower` is the exact canonical rule;
`upper` reverses interval ownership while preserving selector, markers, boundaries,
distractors and tail behavior. Racket-backed seeds 0/1 cover both settings; all
three demonstrations and the query distinguish the opposite setting. This is
finite evidence against one parameter rival and does not change production or
approval state.

The scalar repair narrows only invalid API calls and introduces no measured grid
shortcut because sampled lawful outputs are unchanged. Lesson identifiability is
finite and relative to declared rivals, not a proof against every hypothesis.

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

Source SHA-256: `1157d7044a6f0ec62be9d5eb4138058fa5ad77448c8f2adbe02bfd8c70d04e20`.

# Decisions — `964b23808a3c`

## D1 — Repair scalar validation at the public boundary

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and
`sample_index >= 0`; apply the same contract in both `generate` and
`schedule_profile`.

**Original rationale.** The pinned baseline did not document a reason for
accepting coercible scalar lookalikes. Its validation covered difficulty and
axis names but left seed/index normalization implicit.

**Why this choice.** The official before battery identified 33 strict-scalar
warnings. A negative index silently selected a profile from the end, while
booleans/floats/strings could cross an API boundary despite not being literal
scheduler coordinates. One shared boundary prevents inconsistent behavior
between the scheduler and generator.

**Alternatives rejected.** `int(value)` coercion was rejected because it aliases
values such as `True`, `1.75`, and `"1"`; clamping negative indices was rejected
because it hides caller errors; forbidding negative seeds was rejected because
integer seeds are a lawful deterministic domain and the generator already
handles them.

**Probe and failure mode.** The red run retained 22 expected failures before the
fix. `counterexamples/strict_scalar_contract.json` is exercised by the focused
tests. Remaining limitation: Python integer subclasses are rejected deliberately;
callers must normalize external numeric types explicitly.

## D2 — Keep `VERSION = "3.0.1"`

**Choice.** Do not bump the generation version for a validation-only change.

**Why this choice.** `VERSION` is passed into the deterministic draw context, so
bumping it would change lawful grids even though the repair does not alter the
lawful mapping. A baseline/final comparison found 0 differences in 1,728 lawful
calls, including exact overrides.

**Alternative rejected.** A mechanical patch-version bump would make every
existing lawful sample look changed and would defeat the intended stability
property. This is not a claim of exhaustive equivalence; the retained probe is
finite and source-bound.

## D3 — Leave canonical Racket authority unchanged

**Choice.** Preserve canonical Racket source SHA-256
`2c8f8aa67ae8104f49348542b8fc365527f316c292c87dd8a6c08a0dfd9cc1a0`
and `RULE_HASH = "c7e69da25375"`.

**Why this choice.** The failure occurs before generation/scheduling, not in rule
semantics or labels. Rule smoke, authority sync, canonical replay, and the final
battery all passed.

**Alternative rejected.** Editing Racket or canonical data would be an unrelated
task mutation and could mask the boundary defect.

## D4 — Retain the existing three-demo curriculum

**Choice.** Keep `EXAMPLES_NEEDED = 3` with one query and the existing schedule.
Report both production-order and query-rotation results.

**Why this choice.** The source-bound probe found 0 failures in 2,304 rotations.
The production sampler then materialized 300 lessons (100/band), 1,200 pairs,
and 1,200 rotations with zero ambiguity or scoring/materialization errors. Every
declared rival was refuted in every sampled lesson.

**Alternative rejected.** Adding demonstrations would increase cost without a
measured teaching failure. Reducing demonstrations was not tested and is not
claimed safe.

**Limits.** Finite declared-rival testing does not prove unique induction. The
random census reuses each materialized bundle for rotations and does not
enumerate all seeds or all undeclared hypotheses.

## D5 — Prototype `segment_owner` as the single rule parameter

**Choice.** Build an unapproved episode-level parameter with two settings:
`lower` (canonical/current marker owns the preceding interval) and `upper`
(previous marker owns the following interval). Select it once per episode.

**Why this choice.** It changes a genuine relational reasoning step while
preserving object roles, target selection, marker order, interval boundaries,
distractors, and floating tails. It is smaller and more faithful than combining
multiple structural mutations.

**Alternatives rejected.** Grid size, palette, target count, terminator location,
and distractor density are input-distribution axes rather than rule parameters.
Changing the “last nonzero is 5” selector would alter a separate object-role
predicate and make the variant less controlled. A color permutation was rejected
because colors are marker values, not interchangeable semantic labels here.

**Evidence and failure modes.** `lower` replays 5/5 canonical pairs. Two retained
Racket-backed episodes cover both settings; all three demonstrations and the
query distinguish the opposite rule. This is only two finite episodes against
one parameter rival; it does not establish universal identifiability and does
not add a production parametric API.

## D6 — Keep audit work findings-only

**Choice.** Do not edit `5639e60f0fac` or `321b71aa828c`.

**Why this choice.** The assignment requests adversarial reproduction, not repair.
For `5639e60f0fac`, the taller-template witness is outside the generator's current
self-check domain and is therefore reported as an authority-coverage limitation,
not mislabeled as an incorrect generated label. For `321b71aa828c`, the
fixed-coordinate rival is a direct training-data shortcut because it fits
Racket-labeled generated inputs yet fails a canonical example accepted by
`self_check`.

## D7 — Evidence packaging choices

**Choice.** Package decisive reports, exact counterexamples, command logs, and
the full source-bound lesson census inside the automatic evidence bundle.

**Why this choice.** The return stays below the 25 MiB expanded evidence budget,
and the full census retains exact materialized lessons and rotations rather than
asking a maintainer to reconstruct them from the compact summary. Automatic
bundling keeps the member count within limits while preserving per-file hashes.

## Current overlapping proposal

Unselected older-baseline alternative. Current accepted1157d704 already fixes both scalar entry points,preserves lawful negative integerseeds andversion3.0.1,has1728reported byte-identical valid-call checks,135portable tests anda source-bound lower/upper prototype that remains unapproved. Proposedc586f09a starts fromc8437cf4,collides on generator/tests/notes/prototype,andintentionally bumpsversion3.0.2 to remap lawful RNG draws. Its111reported tests,12/12battery andfour selector/segment settings qualify onlyproposed bytes. Retain the distinct contains_5 extension for a rebase that preserves current valid draw stability andcurrent prototype;no selected source/authority/prototype orapproval change. Fresh345-file runtime-closure replay ispartial scope,notfull extraction. Retained at `workspace/proposals/review-7c9fb5e6a004dbf2/manifest.json`.
