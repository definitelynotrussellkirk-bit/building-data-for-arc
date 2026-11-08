# Working notes: 67aae675d447

## Current decision

Version 2.0.0 samples the full local-frame version of the pinned rule. Colors
2/3/4 are an ordered orthogonal source frame and 5/6/7 are an independently
oriented ordered target frame. Color-8 cells within source-local Chebyshev
radius 3 define the motif; the Racket authority paints the perimeter of the
motif's local bounding box at the target frame. Color-8 cells outside both
radius-3 frame squares are preserved distractors.

The canonical Racket authority did not change. `RULE_HASH` remains
`e0f86f3cb6ab`; the final generator SHA-256 is
`3406acbb2c2873b35b1349859dcdcaa70263634557e717349226d9d4211880a6`.

## Reversed baseline choices

The 1.3.0 generator used three fixed motifs, an always-upright source frame,
four target rotations, dead palette/texture controls, singleton pseudo-axes,
and three invalid negative fixtures inside the advertised ordinary domain. It
also accepted malformed scalar values and unknown override keys, and its
placement loop could fall back to a fixed layout. Those choices were replaced
with constructive generation over eight independently chosen source/target
orientations, exact motif geometry, exact exterior distractor count, strict
call validation, and a pixel observer for every public axis. There is no
fallback path and no advertised invalid texture.

## Public distribution

The eight observable integer axes are:

- `grid_h` 10..24 and `grid_w` 14..24;
- `n_motif` 3..7;
- `bbox_u_span` and `bbox_v_span` 2..6;
- `n_distractors` 0..3;
- `source_orientation` and `target_orientation` 0..7.

A stochastic 3:2 core/broad mixture keeps frequent canonical-shaped examples
(13x19, three motif cells, no distractors) while retaining full support for all
axis values. No fixed lesson schedule is declared. Difficulty only reweights
broad draws; exact overrides have the same meaning in every band.

## Validation and teaching contract

`self_check` reconstructs both frames, rejects malformed grids and unknown
colors, checks disjoint in-bounds radius-3 squares, recovers motif geometry and
distractor count, and enforces the published ranges. `observe_overrides`
recovers all eight axes from returned pixels. `rule_mirror` is a pure Python
oracle used only for focused tests and semantic tooling; labels remain Racket
owned.

Declared rivals are copy-the-motif, corners-only, solid-bbox, and reusing the
source basis at the target. Four executable witnesses cover them. The first
three are lesson competitors and are refuted by every lawful generated example;
the orientation rival is checked as a distribution witness because it can
coincide on some same-orientation draws.

## Evidence and limits

- Before battery: 7 green, 2 advisory, 3 failed (`lint`, `defect_lint`,
  `override`), generator SHA `905d8034...`.
- After battery: 12/12 green, no advisories, on generator SHA `3406acbb...`.
- Portable task tests: 120/120 passed, including all 64 orientation pairs and
  25 canonical/generated Racket parity cases.
- Semantic gate: 600/600 strict draws, 3/3 canonical inputs accepted, 4/4
  witnesses fired, 12/12 four-demo lessons identifiable, and 0/60 ambiguous
  query rotations against declared competitors.
- Override gate: 147,780/147,780 accepted draws across 1,642 cases, zero
  findings/warnings, and unknown keys rejected.

The declared manifold is intentionally narrower than every input the authority
could theoretically execute; it requires exactly one of each frame marker,
3..7 motif cells, nondegenerate 2..6 spans, and at most three exterior
distractors. Finite rival checks do not prove unique induction against every
possible hypothesis. An optional 100-lessons-per-band census exceeded its
1,800-second cap and produced no complete report, so it is not counted as
verification; the completed semantic battery is the retained curriculum
evidence.
## Current reviewer considerations

Source SHA-256: `3406acbb2c2873b35b1349859dcdcaa70263634557e717349226d9d4211880a6`.

# Decisions for 67aae675d447

## 1. Preserve the authority; repair the sampler

**Choice.** Keep the selected Racket program and `RULE_HASH=e0f86f3cb6ab`
unchanged. Repair only the generator, task-local tests/tooling, and notes.

**Rationale and probes.** Canonical examples and rule smoke agreed; the defect
was distribution/contract quality, not label authority. The final Racket parity
tests and authority-sync stage both pass.

**Alternative rejected.** Rewriting the rule to match the old upright-source,
four-rotation generator would have narrowed the task and converted a sampler
shortcut into authority.

**Limit.** Racket remains the only label authority; the Python mirror is test
and semantic tooling.

## 2. Replace fake axes with eight observable controls

**Choice.** Publish dimensions, motif count, two local bbox spans, distractor
count, and independent source/target orientation as the only axes.

**Original choice.** v1.3.0 exposed dead palette/texture options, singleton
palette/count values, locked string pseudo-axes, a three-template `motif` index,
and a four-way target basis.

**Rationale and probes.** `observe_overrides` can recover every new value from
returned pixels. The exhaustive override gate accepted 147,780 draws over 1,642
cases with zero findings/warnings and rejected an unknown key.

**Alternatives rejected.** Keeping palette aliases as “variety” would be
misleading because the rule fixes color roles. Keeping a template index would
measure implementation identity rather than task geometry.

**Failure mode/limit.** The exact Cartesian override battery is expensive; it
verifies the declared domain, not undeclared axes.

## 3. Support the full ordered orthogonal frame family

**Choice.** Enumerate all eight D4 cardinal bases (four rotations and four
reflections) for source and target independently.

**Rationale and probes.** The rule is local-coordinate based. The old fixed
source orientation and four target rotations offered an absolute-screen
shortcut. Tests exercise all 8×8 pairs, and the semantic
`source_basis_at_target` rival is explicitly witnessed.

**Alternative rejected.** Rotations only are insufficient because handedness
can remain a shortcut. Coupling source and target orientation is also rejected;
the examples should teach correspondence between ordered frames.

**Failure mode/limit.** Colors 3/4 and 6/7 are ordered basis markers, not
interchangeable palette roles.

## 4. Construct exact motif geometry instead of selecting templates

**Choice.** Generate 3–7 local motif cells with exact u/v spans 2–6. First
choose a realizable box and opposite-extreme cells, then sample remaining cells.
Frame-marker local cells are excluded.

**Rationale and probes.** This creates many shapes while guaranteeing a
nondegenerate bbox and exact observability. Focused tests compare against an
independent pixel oracle and Racket.

**Alternatives rejected.** Rejection-sampling arbitrary point sets can be slow
and can bias rare exact spans. Fixed templates recreate the baseline shortcut.

**Failure mode/limit.** The sampler deliberately excludes degenerate one-cell or
one-dimensional boxes because they do not teach perimeter versus copy/corners/
solid competitors well.

## 5. Define motif membership by the authority’s local radius

**Choice.** Color-8 cells within source-local Chebyshev radius 3 are motif;
0–3 color-8 cells outside both frame squares are distractors.

**Rationale and probes.** This matches canonical behavior and lets training
examples teach that not every color-8 cell belongs to the source motif. The
observer and self-check independently separate motif and distractors.

**Alternative rejected.** Treating all color-8 cells globally as motif makes
distractors impossible and teaches an overly broad shortcut. Placing distractors
inside the target radius would make the initial target ambiguous.

**Failure mode/limit.** More than three exterior distractors and color-8 cells
inside the target square are outside the declared generator manifold.

## 6. Construct disjoint in-bounds frames; remove fallback

**Choice.** Select origins whose radius-three squares fit and are separated by
Chebyshev distance at least 7. Cache feasible origin sets but sample positions
per call.

**Rationale and probes.** Every exact override combination has a lawful
construction, so a hidden fallback is unnecessary. `self_check` rejects
intersection and target contamination.

**Alternative rejected.** The old 60-try loop plus fixed fallback could silently
change requested geometry and concentrate data.

**Failure mode/limit.** Published minimum dimensions are chosen so two such
frames and requested distractors are always constructible.

## 7. Use a stochastic core/broad curriculum

**Choice.** Draw `core` three times and `broad` twice in a private five-entry
weighted choice. Core strongly favors the canonical 13x19, three-cell,
span-(3,2), zero-distractor profile; broad retains all values, with difficulty
only reweighting size/complexity.

**Rationale and probes.** The profile floor now records 31/60 exact canonical
shape/palette hits, with at least 10 in every band, while diversity remains
100% unique inputs/outputs in the standard probe.

**Alternative rejected.** A deterministic period was briefly considered, but
claiming one adds a schedule-enumeration obligation and is unnecessary because
each lawful demo independently refutes the three lesson competitors. Uniform
sampling alone underrepresented the canonical profile in the baseline.

**Failure mode/limit.** This is a stochastic distribution, not a promise of an
exact ratio in every small batch.

## 8. Fail loudly on bad calls

**Choice.** Reject booleans/floats/strings for integer fields, negative
`sample_index`, out-of-range overrides, and unknown keys.

**Rationale and probes.** Baseline defect lint found 23 invalid scalar cases and
the override gate showed unknown keys were swallowed. Focused tests watched
these cases fail before implementation.

**Alternative rejected.** Silent coercion or ignoring unknown values makes
training recipes unreplayable and allows misspelled controls to look successful.

## 9. Make semantic claims executable

**Choice.** Provide a pure rule mirror, four named rivals, four witnesses,
witness-to-rival mapping, three lesson competitors, and `lesson_identifiable`.

**Rationale and probes.** The final semantic gate measured 600/600 strict draws,
all four witnesses, 12/12 identifiable four-demo lessons, and 0/60 ambiguous
rotations. The test suite verifies purity and nonmutation.

**Alternative rejected.** Narrative rival comments were present in v1.3.0 but
could not be checked. A fixed schedule designed merely to force witnesses was
unneeded because the three teaching rivals disagree on every lawful example.

**Failure mode/limit.** Declared rivals are finite. The orientation rival can
agree when frames share a basis, so it remains a distribution witness rather
than a required per-demo competitor.

## 10. Add an independent probe rather than test internals

**Choice.** Build `workspace/reference_probe.py` to rediscover frames and local
geometry from pixels and to run Racket parity.

**Rationale and probes.** Tests should fail if observable behavior changes, not
because private helper names change. The probe also gives later agents a compact
oracle/observer/witness toolkit.

**Alternative rejected.** Importing private generator helpers in every test
would duplicate implementation assumptions and weaken the regression value.

## 11. Stop at verified task scope

**Choice.** Do not broaden colors, radius, or malformed-frame semantics beyond
the canonical task; do not count the timed-out optional 300-lesson census.

**Rationale.** The completed battery and 120 tests establish the claimed public
manifold. Expanding further would be speculative and could dilute canonical
support.

**Remaining uncertainty.** Finite declared-rival evidence does not establish
universal identifiability. The optional larger census timed out without a
complete result and is reported only as a non-result.
