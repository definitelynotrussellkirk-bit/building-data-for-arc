# Working notes: 4cfd24806fb2

## 2026-10-02 review — assignment `review-26b93273c50da0e8`

### Baseline defects reproduced

The `1.2.1` generator produced generally valid mirror scenes, but its declared control surface and training semantics were unreliable:

- it omitted the canonical `RULE_HASH` pin;
- `position_bias` and `density` were singleton/dead axes;
- `palette_kind`, `palette_size`, and `n_distinct_colors` did not causally control the returned grid;
- `texture` mixed helpful aliases with three intentionally malformed scenes and allowed those malformed scenes through the advertised legal domain;
- unknown overrides were silently accepted;
- `self_check` accepted multiple dividers, stray gray cells, one-color/one-distance lessons, and occupied mirror destinations;
- the generator declared shortcut intent only in comments, with no executable rivals, witnesses, or lesson-identifiability gate;
- only 1 of 60 pinned draws hit an exact canonical `(height,width,palette-size)` profile, and hard had zero support.

Evidence: `checks/before/checks/4cfd24806fb2_before_battery_summary.json`, the baseline lint/defect/override logs, and the baseline profile-floor JSON.

### Selected repair

The broad but misleading axis surface was replaced by one exact observable axis, `scene_profile`. Four deliberately complementary profiles are scheduled by `(seed + sample_index) % 4` so a normal four-example lesson is guaranteed to contain:

- one exact canonical anchor;
- one off-center divider with connected/color-9 sources;
- one dense edge/same-row motif with more than six sources;
- one scene with unrelated right-side distractors.

The generator now rejects unknown difficulties/overrides, returns fresh deterministic grids without touching global RNG state, and enforces a mutation-sensitive grammar through `self_check`.

### Executable semantic contract

`expected_output` is a Python audit mirror only; the synchronized Racket program remains output authority. The contract adds:

- `strict_canonical_like` and `MIN_STRICT_FRAC = 0.20`;
- six witnesses: off-center divider, right distractors, color-9 source, >6 sources, connected sources, and multiple divider distances;
- eight named rival rules;
- six rivals that fit every canonical pair and therefore require generated counterexamples;
- `lesson_identifiable`, which rejects a lesson if any named competitor survives all demonstrations;
- mutation fixtures covering missing/duplicate divider, no sources, one-distance sources, occupied destinations, and stray gray.

### Measured after-state

- full battery: 12/12 stages green;
- semantic census: 600/600 generated successfully, 125/600 strict (20.8%), all 5 canonical inputs accepted, 6/6 witnesses firing, 6/6 rival claims verified, and 12/12 lessons identifiable;
- profile-floor census: 16/60 exact canonical-profile hits and nonzero exact support in easy/medium/hard;
- reusable 60-draw probe: exactly 15 draws per profile, 25% strict in each band, no `self_check` failures, and every canonical-fitting shortcut refuted;
- task-local regression suite: 9 tests pass.

Evidence: `checks/after/`, `workspace/profile_probe_after.json`, and `tests/`.

### Limits retained deliberately

- The generator assumes exactly one full-height gray divider and initially empty mirror destinations. It does not attempt to define collision precedence outside that grammar.
- `preserved_right_noise` broadens the scene beyond the canonical examples, but only to test the authoritative rule's explicit preservation behavior; it occupies one of four scheduled profiles.
- Canonical anchors match canonical structural profiles rather than replaying exact canonical grids, avoiding memorization while preserving a measurable profile floor.
- The Python audit mirror is not a second authority and should not be used to rewrite the pinned Racket rule.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e042ff7045afe3861e289839684bfa6d9797463ebffe13a59d44b1d1e54fd395`.

# Decisions: 4cfd24806fb2

## D1 — Preserve the Racket authority

**Input choice.** Keep the synchronized Racket program unchanged and add `RULE_HASH = b5a5db408e2f` to the generator.

**Original rationale.** The original module omitted the pin. No evidence suggested the transformation itself was wrong: baseline `rule_smoke`, `racket_lint`, and `authority_sync` were already green.

**Alternatives considered.** Rewrite the Racket program for stronger validation; make the Python mirror authoritative; alter collision behavior.

**Probe.** Before and after `rule_smoke`, `racket_lint`, and `authority_sync`; all canonical pairs checked by regression tests.

**Failure modes / limit.** Racket is intentionally defined only on the generated/canonical grammar. Python `expected_output` could drift in the future, so tests pin both canonical outputs and the rule hash; it is not a replacement authority.

## D2 — Replace nine misleading axes with one honest semantic axis

**Input choice.** Remove `grid_h`, `grid_w`, `palette_kind`, `n_cells`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` from the public override surface. Expose only exact `scene_profile`.

**Original rationale.** Unknown. The old docstring called the controls “combinatorial axes,” but several were unused, singleton, mutually inconsistent, or aliases; three legal texture values deliberately produced invalid examples.

**Alternatives considered.** Repair every old axis independently; keep aliases for compatibility; leave dimensions/counts as exact axes.

**Why rejected.** A Cartesian product of low-level knobs creates many invalid or semantically redundant combinations and makes lesson quality accidental. There was no retained consumer contract requiring those names. One profile axis is observable, testable, and maps directly to pedagogical purpose.

**Probe.** Override battery: 450 accepted probes, exact round trips for all four values, zero findings; unknown and invalid values reject in regression tests.

**Failure modes / limit.** Callers relying on undocumented old overrides will now receive an explicit error rather than a silently unrelated grid. This is deliberate fail-closed behavior.

## D3 — Use four complementary profiles rather than weighted random features

**Input choice.** `canonical_sparse`, `off_center_cluster`, `edge_row_motif`, and `preserved_right_noise` form a deterministic four-example cycle.

**Original rationale.** The old comments claimed that four varied demonstrations should defeat midpoint/right-to-left/color/erase rivals, but ordinary generation did not guarantee those properties.

**Alternatives considered.** Independent Bernoulli feature flags; weighted random profile selection; more than four profiles; exact replay of the four canonical demonstrations.

**Why selected.** Four profiles match `EXAMPLES_NEEDED = 4`, give each demo one clear teaching role, and guarantee coverage without rejection sampling. Independent flags can accidentally omit a crucial counterexample or combine too many novelties in one scene. Exact replay encourages memorization and would not refute all canonical-compatible shortcuts.

**Probe.** Fixed-seed schedule test and 60-draw workspace census; all profiles occur exactly 15 times, and every four-example scheduled lesson is identifiable.

**Failure modes / limit.** A deterministic cycle can be aliased by an external sampling schedule. The initial `sample_index % 4` implementation did alias with the profile gate's pinned indices; switching to `(seed + sample_index) % 4` restored support in every band.

## D4 — Make one quarter of lessons canonical anchors

**Input choice.** `canonical_sparse` chooses among all five canonical dimension profiles and reproduces canonical source-count/color-count multiplicity without copying exact grids.

**Original rationale.** Baseline profile-floor support was only 1/60 exact and zero in hard, creating a domain-gap risk.

**Alternatives considered.** Replay exact public grids; use only the most common canonical dimensions; remove broad difficulty-dependent scenes.

**Why selected.** Structural anchors retain the real size, divider, palette-size, and one-repeat source-color pattern while varying positions/colors. This raises support without training on exact answers.

**Probe.** Profile-floor battery improved to 16/60 exact and nonzero exact support in every band; semantic strict rate is 125/600 (20.8%) against a declared 20% floor; independent probe is 25% in each band.

**Failure modes / limit.** The anchor predicate intentionally checks canonical structure, not exact source coordinates. It cannot guarantee visual identity to a particular public example and should not be interpreted as exact replay.

## D5 — Include an off-center, connected, color-9 case

**Input choice.** `off_center_cluster` places the divider away from the nominal midpoint and guarantees connected sources including color 9.

**Original rationale.** The old comments named the midpoint shortcut but did not make off-center coverage a scheduled invariant. Color cycling could also make a finite-prefix/capped-color shortcut attractive.

**Alternatives considered.** Only randomize divider position; create separate off-center, connected, and color-9 profiles.

**Why selected.** Combining these compatible facts gives one high-information example without obscuring the rule. A separate profile for each would exceed the four-demo budget.

**Probe.** Witness counts in the semantic gate and profile probe; midpoint and ignore-color-9 rivals are directly refuted.

**Failure modes / limit.** Connectedness is not semantic; it is a counterexample to an isolated-points-only learner. The profile must not dominate the curriculum, hence one slot in four.

## D6 — Include a dense edge/same-row/>6-source motif

**Input choice.** `edge_row_motif` exercises top/bottom edges, multiple sources in one row, connected cells, multiple divider distances, and more than six sources.

**Original rationale.** The canonical set is sparse enough that a model can cap the number of copied cells or infer isolated-object processing.

**Alternatives considered.** Raise source count in every profile; add random dense noise; use one huge connected rectangle.

**Why selected.** A dedicated case refutes finite-prefix, isolated-only, and one-per-row shortcuts while leaving the other profiles visually simple. Random noise would make the intended correspondence harder to inspect.

**Probe.** `more_than_six_sources`, `connected_source_cells`, and `multiple_source_distances` witnesses; cap-at-six rival refuted on 35/60 workspace draws.

**Failure modes / limit.** Dense scenes are harder than canonical examples and can increase perceptual burden. They remain one quarter of scheduled examples.

## D7 — Preserve unrelated right-side distractors

**Input choice.** `preserved_right_noise` adds two or more right-side cells that are not mirror destinations and requires them to remain unchanged.

**Original rationale.** Canonical inputs have blank right halves, so at least three simpler rules fit them: clear the right, require blank right, or mirror both directions.

**Alternatives considered.** Keep right half blank; place distractors on mirror destinations; add a separate output-only annotation.

**Why selected.** Noncolliding distractors test the authority's preservation semantics without inventing collision precedence. They refute three canonical-compatible shortcuts in one case.

**Probe.** Semantic gate reports the witness in 159/600 draws and verifies all three rival claims; workspace probe refutes each on 15/60 draws.

**Failure modes / limit.** This is a lawful extrapolation rather than a pattern shown by canonical inputs. It is isolated to one profile, documented, and checked against the unchanged Racket authority.

## D8 — Fail closed on ambiguous grammar

**Input choice.** Require exactly one divider, no stray gray, at least three sources, at least two source colors and distances, in-bounds mirrors, and empty mirror destinations.

**Original rationale.** The old `self_check` only required some full-height gray column and at least one left source; it chose the first divider and ignored collisions/ambiguity.

**Alternatives considered.** Accept degenerate scenes as negative examples; define no-op behavior for no-source cases; allow collisions and let Racket overwrite.

**Why selected.** Training rows need an unambiguous, learnable input-output contract. Malformed negatives belong in tests, not the positive generator distribution.

**Probe.** Mutation fixtures plus explicit regression impostors; final self-check and defect-lint stages green.

**Failure modes / limit.** The generator no longer teaches how to handle collisions, multiple dividers, or source-free inputs; those cases are intentionally outside its domain.

## D9 — Encode rivals and witnesses as executable functions

**Input choice.** Add eight rivals, six witnesses, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable`.

**Original rationale.** The old module had only prose comments naming some rivals; comments cannot prove that generated lessons refute them.

**Alternatives considered.** Rely solely on distribution statistics; compare only against canonical outputs; invoke an LLM as a judge.

**Why selected.** Deterministic executable rivals are cheap, reproducible, and provide exact counterexamples. The semantic gate can verify both witness firing and actual output disagreement without a model call.

**Probe.** Final semantic gate: 6/6 witnesses firing, 6/6 rival claims verified, 12/12 lessons identifiable. Regression tests also prove every declared canonical shortcut fits all five canonical pairs before requiring a generated refutation.

**Failure modes / limit.** The list cannot cover every possible shortcut. The `1c1b8aa6505e` audit demonstrates that declared-rival gates can miss an undeclared proxy, motivating the additional automated gate proposed in `QUESTION_ANSWER.md`.

## D10 — Keep a reusable probe beside the generator

**Input choice.** Add `workspace/profile_probe.py` and retain its JSON result.

**Original rationale.** Battery summaries are authoritative but broad; maintainers need a fast task-specific census of schedule balance, strict support, witnesses, and shortcut refutations.

**Alternatives considered.** Put all assertions only in pytest; add another shared framework script.

**Why selected.** A self-contained task-local probe is easy for later reviewers to rerun or extend and does not change shared tooling.

**Probe.** `profile_probe_after.json`: 60 draws, 15 per profile, 25% strict in every band, no self-check failures, all witness and shortcut counters nonzero.

**Failure modes / limit.** Sixty deterministic draws are a census sample, not a proof over all seeds. The larger semantic gate supplies an independent 600-draw sample.
