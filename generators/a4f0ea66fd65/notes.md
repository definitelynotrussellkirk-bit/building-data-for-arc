# Working notes: a4f0ea66fd65

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-28 exact-vector curriculum review

- The v3.0.0 generator passed the complete twelve-stage baseline, but every
  generalized vector still used absolute magnitudes 2 and 3. A wrong solver
  that read only marker signs/orientation and snapped the displacement to a
  signed 2x3 vector matched 432/432 sampled scenes and survived 216/216
  four-demo schedule windows (`checks/a4f0ea66fd65_before_vector_shortcut_audit.json`).
- Version 3.1.0 keeps the canonical Racket rule unchanged and interleaves two
  generalized profiles among the four canonical anchors. Generalized vectors
  now include axis-aligned displacement and exact distances 1/4 or 4/1.
- Every contiguous four-demo schedule window contains both clear/overwrite
  evidence, both canonical directions, and at least one generalized exact-vector
  counterexample. The same audit now finds 144/432 single-scene counterexamples,
  75 axis-aligned scenes, and 0/216 surviving quantized-shortcut windows.
- Executable `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, and
  `CANONICAL_SHORTCUTS` make the shortcut claims independently checkable. Positive
  morphology-only witnesses are explicitly separated as `BRANCH_WITNESSES`.
- `workspace/vector_shortcut_audit.py` can compare any generator revision with
  `--generator PATH`; it reports vector support and all sliding-window survivors.
- The Racket authority, canonical rows, and selected base authority were not changed.
  This remains a candidate source repair pending normal independent intake review.
## Current reviewer considerations

Source SHA-256: `941bff594233e1f3d26e32af4c6f924bc8a5d278501bf91f24820c64fad0c39c`.

# Decisions for `a4f0ea66fd65`

Assignment: `review-eb9c83c79a62b513`
Baseline generator: `3.0.0`
Candidate generator: `3.1.0`
Canonical rule pin: `a5767619a475`

## Design brief

Preserve the canonical vector-copy rule and the already-correct scene grammar. Repair the measured lesson-level ambiguity by making exact marker distance, rather than a memorized 2-by-3 displacement family, necessary in every four-demo lesson. Keep all existing override domains realizable and make every semantic claim executable.

## D1. Keep the canonical Racket rule unchanged

**Choice.** Do not alter `program_solution`, the selected base authority, or `RULE_HASH`.

**Original rationale.** Prior work synchronized the canonical and selected task-local authority and established the overwrite branch. The baseline canonical regression, rule smoke, Racket lint, and authority-sync stages were green.

**Alternatives considered.** Rewrite the Racket program for readability; add explicit in-bounds checks; change overwrite semantics.

**Why rejected.** None addressed the observed defect. The rule already applies the exact red-to-green vector, preserves source and markers, and overwrites decoy cells exactly as the canonical test requires. A rule edit would add source-sync risk without improving data value.

**Probe.** All five canonical pairs match `rule_mirror`; after authority sync and Racket smoke remain part of the retained battery evidence.

**Failure modes and limitations.** The Python mirror is not the authority. Its parity is protected by canonical exactness and the Racket battery, but future rule edits must rerun both.

## D2. Treat signed/oriented 2-by-3 quantization as the primary rival

**Choice.** Add an executable `quantized_2x3` rival that reads marker direction and orientation but replaces exact distances with the canonical magnitudes 2 and 3.

**Original rationale.** Unknown; v3.0.0 described its last two slots as generalized vectors, but every vector still had absolute magnitudes `{2,3}`.

**Alternatives considered.** Check only fixed `(2,3)` and `(2,-3)` rules; rely on vector-count diversity; rely on canonical-profile support.

**Why chosen.** The rival is strictly more plausible than a fixed-direction shortcut: it uses both marker signs and whether the vertical or horizontal component is larger. It therefore fits diagonal vectors such as `(3,2)`, `(-3,2)`, and `(-2,-3)` while still ignoring the exact displacement.

**Probe.** `workspace/vector_shortcut_audit.py` run against the untouched ZIP reports 432/432 single-scene matches, 0 axis-aligned scenes, and 216/216 surviving four-demo windows. The twelve-stage baseline nevertheless reported all green.

**Failure modes and limitations.** This is a human-selected rival, not an exhaustive model-error taxonomy. Future model traces may expose different shortcuts and should be added as named rivals.

## D3. Broaden generalized vectors beyond magnitudes 2 and 3

**Choice.** General profiles now draw from band-specific sets containing `(0,±4)`, `(±4,0)`, and signed `(1,4)` / `(4,1)` variants.

**Original rationale.** The old generalized vectors varied signs and swapped component orientation, apparently to move beyond the two public directions while remaining easy to place.

**Alternatives considered.** Use arbitrary random nonzero vectors; add only one distance-4 diagonal; use magnitudes 5 or 6; change marker colors or add more markers.

**Why chosen.** A small enumerated set gives deterministic support guarantees, remains compatible with 8×8 grids and 3×3 source bounding boxes, and separately teaches two facts: vectors may be axis-aligned, and marker distance must be read exactly. Magnitude 4 is large enough to refute the 2/3 rival without creating avoidable placement failures.

**Probe.** The focused tests exercise all bands and both general profiles. A 40-seed stress census generated every default slot without failure. Boundary probes realized every scene profile with `grid_h=8`, `grid_w=8`, and source sizes 3 and 8.

**Failure modes and limitations.** The generated vector family is still finite and capped at magnitude 4. It establishes exact-vector reasoning over a useful local support set, not arbitrary unbounded translation.

## D4. Interleave general profiles so every four-demo window is decisive

**Choice.** Reorder the six-slot cycle to:

1. `canonical_right_clear`
2. `general_overwrite`
3. `canonical_left_clear`
4. `canonical_right_overwrite`
5. `general_clear`
6. `canonical_left_overwrite`

**Original rationale.** v3.0.0 placed four canonical slots first and both general slots last. That preserved canonical support but allowed some short windows to contain no meaningful exact-distance evidence.

**Alternatives considered.** Increase `EXAMPLES_NEEDED` to five or six; randomize profile order; use a four-slot cycle; leave order unchanged and hope the query distinguishes the shortcut.

**Why chosen.** General slots at residues 1 and 4 are never more than three positions apart. Every four-consecutive-demo window therefore includes at least one exact-distance counterexample, at least one clear scene, at least one overwrite scene, and both canonical directions. The guarantee is structural rather than probabilistic.

**Probe.** Tests exhaust all six start residues, three bands, and three seeds. Every window refutes every declared competitor. The custom audit reports zero surviving quantized or declared-rival windows over 216 deterministic windows.

**Failure modes and limitations.** The guarantee assumes consumers preserve consecutive `sample_index` blocks, as the repository runner does. A downstream sampler that selects arbitrary independent indices should run its own lesson-level rival audit.

## D5. Bind canonical dimensions and source sizes to profiles, not old slot positions

**Choice.** Replace positional dimension/size arrays with profile-keyed contracts. The four canonical profiles retain their prior 8×10/11/12 and 9×12 anchors and source sizes 3–5; general clear/overwrite retain source sizes 6/8 and their band-specific larger canvases.

**Original rationale.** The old positional arrays made sense only while the profile order was fixed.

**Alternatives considered.** Reorder the arrays in parallel; make all dimensions random; add dimensions as another schedule cycle.

**Why chosen.** Profile-keyed defaults prevent a future reorder from silently assigning an 8-cell general object to a small canonical anchor or degrading strict canonical support. They also make explicit `scene_profile` overrides choose coherent defaults.

**Probe.** Focused tests assert each canonical profile's dimensions and source size by name. The override boundary test covers all profiles and all bands. The profile-floor battery remains above its declared floor.

**Failure modes and limitations.** `decoy_color` still alternates by sample-index residue rather than profile. This is deliberate because color is semantically irrelevant and both values remain present in every full cycle.

## D6. Declare executable rivals, canonical shortcuts, and honest witnesses

**Choice.** Add seven `SEMANTIC_RIVALS`, use all seven as `LESSON_COMPETITORS`, declare the two public-equivalent distance shortcuts as `CANONICAL_SHORTCUTS`, map five semantic witnesses to concrete rivals, and classify six morphology-only predicates as `BRANCH_WITNESSES`.

**Original rationale.** v3.0.0 had nine positive witnesses and an internal candidate-output helper, but no declaration connected them. The baseline semantic gate therefore reported 12/12 lessons identifiable with `competitors_declared: []` and could not name or test the surviving rule.

**Alternatives considered.** Keep only natural-language witness labels; map every positive feature to a synthetic rival; declare only the new quantized rival.

**Why chosen.** A witness should either prove a branch is present or prove a named wrong rule disagrees—never blur the two. Executable declarations let the strict semantic gate independently verify every claim and test public-equivalent shortcuts against generated counterexamples.

**Probe.** The strict after semantic gate reports all 11 witnesses firing, 5/5 rival claims verified, both canonical shortcuts refuted by `exact_marker_distance`, and 12/12 lessons identifiable across all bands.

**Failure modes and limitations.** Rival solvers use the task's lawful input assumptions. They are not intended as robust general-purpose solvers for malformed grids.

## D7. Make `lesson_identifiable` require demo-side refutation

**Choice.** A lesson is accepted only when every declared competitor is contradicted by at least one demonstration, the intended output matches every demo/query, vectors vary, and both clear and overwrite behavior are shown.

**Original rationale.** The previous hook intersected a private candidate set and rejected only shortcuts that survived demos *and changed the query*. An answer-equivalent query could hide that the demonstrations never taught the intended distinction.

**Alternatives considered.** Keep query-only discrimination; require merely two vectors; defer entirely to the generic semantic gate.

**Why chosen.** Training supervision comes from demonstrations. Requiring demo-side refutation prevents a lesson from being labeled identifiable just because the particular query happens to collapse two rules to the same answer.

**Probe.** The task-local test enumerates all schedule residues. The generic semantic gate independently scores `LESSON_COMPETITORS` and agrees with the hook on all twelve pinned lessons.

**Failure modes and limitations.** This is intentionally stricter than answer-identifiability for a single query and could reject a lesson that is harmless for that one answer. For training data, that conservatism is desirable because the goal is rule learning, not accidental query equivalence.

## D8. Add a reusable vector-shortcut audit

**Choice.** Add `workspace/vector_shortcut_audit.py` with `--generator`, `--seeds`, and `--out` options. It reports vector/profile histograms, axis-aligned support, single-scene rival matches, and sliding-window survivors.

**Original rationale.** No existing generic gate summarized exact displacement support or tested a synthesized signed/oriented quantization rival.

**Alternatives considered.** Keep a one-off notebook; encode the probe only in tests; modify shared tooling from this task-scoped assignment.

**Why chosen.** A task-local CLI is reproducible, source-bound, cheap, and safe to return. `--generator` makes before/after comparison possible without mutating the checkout.

**Probe.** The tool fails on the untouched generator with the measured 432/432 and 216/216 ambiguity, then passes on v3.1.0 with 144 exact-distance counterexamples, 75 axis-aligned scenes, and zero surviving windows.

**Failure modes and limitations.** It uses the Python mirror for high-volume scoring. Canonical Racket parity is established separately by the retained battery; the tool should not replace that authority check.

## D9. Repair the schedule-dependent mutation fixture and make focused tests portable

**Choice.** Change the protected-target mutation from relocating the green marker to placing cyan on an existing translated target, locate the runtime root dynamically, and reuse one Racket bridge for all residue tests.

**Original rationale.** The original mutation attempted to place green on an old target, but moving green also changed the vector. It happened to fail under the old profile order and became a valid grid after reordering.

**Alternatives considered.** Delete the fixture; pin it to a different sample index; accept a duplicate-marker mutation.

**Why chosen.** The new mutation keeps the marker vector fixed and is invalid for the intended reason under any profile order. Dynamic root discovery lets the same test run in the source tree and staged runtime. Reusing one bridge avoids repeated Racket startup costs.

**Probe.** The new tests were observed red before implementation. The final focused suite passes 14/14 in the staged runtime with the protected Racket executable.

**Failure modes and limitations.** The standard twelve-stage battery does not currently execute task-local pytest files; this gap is recorded in `FEEDBACK_TO_CODEX.md`.

## 2026-10-25 native parametric handoff

The production generator and canonical authority were intentionally left unchanged. The current generator SHA-256 is `941bff594233e1f3d26e32af4c6f924bc8a5d278501bf91f24820c64fad0c39c`; the exact canonical Racket program SHA-256 is `7c31c8df4afb12a5c3cfec8da2087b6e655c14e39c247c4acf008c36310e9722`.

A task-local native family now exposes episode-fixed `copy_extent`. `single` is byte-identical to the canonical rule. `decoy_size` identifies the connected color-6/7 decoy, measures its occupied size, and uses that input-derived count to paint successive red-to-green vector translations of the cyan source. The sampler supports 2–6 demonstrations and four prefix-stable queries, including a substantive 30×30 case whose fourth translated copy reaches the lower-right boundary.

Final retained checks: 20/20 staged tests; a 32-seed finite declared-rival audit covering 192 episodes and 1,472 labeled pairs with no harmful survivor; protected-Racket qualification at 2, 3, and 6 demonstrations (32 + 40 + 64 executions); 16 saved one-query public views; and a protected counterfactual replay whose fixed-three intermediate changes 8 final cells. `checks/handoff-validation.json` independently rehashes and reconciles all bound artifacts. The staged suite still emits two pre-existing portability warnings for a retained legacy test; they do not fail execution and were not modified because they are outside this native family.

Status is reviewer-ready only. The next action is exact-byte owner integration followed by fresh native qualification, causal replay, and owner acceptance; no training admission is implied.
