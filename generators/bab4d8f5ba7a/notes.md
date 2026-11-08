## Current native parametric decisions — review-a2fa8bcede5fa990

**Reviewer-ready; exact-source owner acceptance is pending. No training admission.**
This work adds a native episode family under `workspace/parametric/`; production
version 3.0.0 remains unchanged at SHA256
`6b48b50cfbabd0a320318c122f6c77f8b90e8de052e20cfa2e622eab6bdeae02`.
The existing canonical rule and approval records are preserved.

### Rule, grammar and teaching decisions

- `{"mode":"row"}` preserves the exact 237-byte canonical program. It recolors
  every body 8 using its own nonzero row header, preserving all other cells.
- `{"mode":"largest"}` executes that recoloring first, recomputes same-color
  nonzero four-connected components, selects greatest occupied area, and renders
  only that component's tight support. Ties compare each component's first actual
  occupied coordinate lexicographically, not independent bounding-box minima.
  Empty foreground returns `[[0]]`.
- Both settings admit every built-in rectangular list grid with axes 1..30 and
  exact integer colors 0..9, including the original examples, blank grids,
  one-column cases, color-8 headers, ties, holes and arbitrary clutter. The
  proposed unique-largest restriction was rejected because it excluded every
  original canonical input. The explicit occupied-anchor tie rule retains them.
- The first two demos are complete teaching cores, independent of the production
  five-step sample-index schedule. Core 0 changes the winner from 16 to 23 cells
  by merging a checkerboard of keys and markers; Core 1 breaks an original
  21-cell 8 component and resolves three 16-cell ties. They expose global-color,
  original-component, connectivity, header-guard, tie and rendering shortcuts.
- Independent controls support 2–6 demos and 1–4 queries. Ordinary generation
  defaults to three demos; native qualification explicitly exercised the minimum
  two demos with four queries. Separate settings/demo/query random streams build
  full six/four banks before slicing, with identical inputs across settings and
  fresh output lists. Source query roles are seed-shuffled before prefix selection;
  the public exporter separately retains its presentation permutation privately.
- The 30×30 demo and query have 630 and 619 occupied cells, respectively. Their
  merged combs contain 180 and 169 cells; the competing solid patch has at most
  64 cells. Balanced tooth rows and a dense fragmented color field populate all
  four quadrants. These are substantive large scenes, not padded small motifs.

### Current exact identities

- Canonical program SHA256:
  `071b2a298d5c565c469357c6b6662d4fe94ec5e123bbe48fa36861d8e40691df`.
  The recorded production rule hash `1130750019d1` uses normalized source.
- Alternative program SHA256:
  `de16b74d3855da7d5c774cd6da863622e0376a0339e36ed0cce8798939916b0d`.
- Native implementation SHA256:
  `531729bc65b9ea355e0116284241838008b50edfb9642ca989f920984a39e013`.
- Native 13-file manifest SHA256:
  `dbec78b8d22972fb126e96b1a429a7959d0516fe2d74de32b4bc47d15bb9d8a4`.
- Qualification execution SHA256:
  `ddedd84b00598b6a9accba6a0d19c1d4480ecfae980fc1dfe560d95ab19d6682`.

### Evidence actually exercised

All paths below are relative to the return's `WORK/` evidence layout.

- `checks/bab4d8f5ba7a/native-and-audit-command.json` and
  `checks/bab4d8f5ba7a/native-and-audit.xml`: **112 current tests passed** (50 native plus 62 audit).
  Earlier red receipts remain separate and are not added to passing coverage.
- `checks/bab4d8f5ba7a/sampler-v1.json`: **96/96 requests succeeded**, with
  149 distinct inputs, 64 distinct query inputs and 32 distinct 30×30 inputs.
- `checks/bab4d8f5ba7a/teaching-v1/private/audit.json` and `checks/bab4d8f5ba7a/teaching-v1/private/executions.jsonl`:
  40 intended labels; **108 fits, 104 refuted, four intended-only survivors**;
  all 16 survivor-query scores agree. The audit used only the first two demos
  to fit, froze survivors before query scoring, and retained 272 requests,
  176 protected Racket evaluations and 96 cache hits. Current task/runtime
  source closure remained unchanged.
- `checks/bab4d8f5ba7a/qualification/qualification.json` with sibling
  `checks/bab4d8f5ba7a/qualification/execution.json`: **qualified**, four jobs, two demos/four queries, 32 protected
  evaluations. This is reviewer qualification, not owner acceptance.
- `checks/bab4d8f5ba7a/causal-recipe.json`, `checks/bab4d8f5ba7a/causal/witness.json` and
  `checks/bab4d8f5ba7a/causal/replay.json`: both teaching cores have a replayed skip-A control.
  Four protected intermediate executions retain the recolored state and selected
  component; replacing only the stage with the original input changes both final
  outputs while B's component selection and renderer remain byte-identical.
- `checks/bab4d8f5ba7a/preview/private/manifest.json`,
  `checks/bab4d8f5ba7a/preview-export-command.json` and `checks/bab4d8f5ba7a/preview-verify-command.json`: four episodes
  and 16 one-query public views exported and verified. Private settings, source
  indices, programs, answers and future queries remain with the consumer.
- The independent fixed-scene design probe remains in
  `checks/bab4d8f5ba7a/design_component_probe.py` and its JSON report. A subsequent
  read-only review of the frozen native implementation, adapter, contract,
  README and native tests found no Critical, Important or Minor issues; it
  performed no additional test run.

### Limits and owner next action

Finite seeds, scenes and named rival programs do not establish universal rule
identifiability, exhaustive correctness or measured training gain. The new
whole-episode teaching construction avoids the old stride-five scheduling
assumption locally, but does not repair or resolve the unchanged production
schedule. Both inherited findings remain `needs_triage`:
`review-6f4e0d954f1fab47:v0001` and `review-db674f1f2060195b:v0001`.

The owner should separately qualify and accept this exact integrated native
source through the existing native route. Keep `ready` distinct from `accepted`;
no approval or training admission follows from these reviewer receipts.

---

# Working notes: bab4d8f5ba7a

## Review `review-6ad1d9e4249d4614`

### Authority

- Canonical rule retained unchanged.
- `RULE_HASH = 1130750019d1`.
- Racket authority, base target, and archival raw source form one exact group.
- Racket execution and Python mirror agree on all canonical pairs and 120 generated inputs.

### Distribution decisions

- Replaced false independent size/count axes with six exact scene profiles.
- Replaced inert palette metadata with three observable column-zero patterns.
- Replaced random semantic branch occurrence with a five-step sample-index schedule.
- Removed `no_headers`, `no_markers`, and `header_is_eight` from ordinary training generation.
- Preserved the useful intent of version 2.1.1: multi-marker rows test “recolor all,” and a marker in a headerless row tests the zero-header guard.
- Added inert non-cyan body cells to test preservation rather than row reconstruction.

### Rejected approaches

- Do not clamp independent overrides; the returned grid must exactly materialize every accepted value.
- Do not accept unknown override keys; a typo must fail loudly.
- Do not use identity-only cases as ordinary variety.
- Do not rely on random probabilities for semantic branch coverage.
- Do not treat a positive witness as sufficient unless it refutes a named executable rival.
- Do not modify the canonical rule merely to add generated counterexamples.

### Evidence

- Before battery: 5 green, 1 advisory, 6 failed.
- After battery: 12/12 green.
- Focused TDD: initial 8 failures; later rival-binding test failed as intended; final 9 passed.
- Override contract: 7,020 accepted draws, zero findings/warnings, unknown key rejected.
- Semantic gate: 600 draws, strict rate 38/600, five witnesses firing, five rival claims verified.
- Rule smoke: 120 applications, zero crash/identity/mutation, 120 mirror matches.

### Future checks

- Run a gate on actual packed/sharded lesson windows; stride-five sharding can defeat the five-profile local curriculum even when corpus-wide counts are good.
- Rerun authority sync and mirror parity after any Racket source or rule-hash change.
- Add a new semantic rival when model errors reveal a recurring shortcut not represented by the current four.
- Keep axis domains explicit literals unless the static evaluator gains safe support for derived domains.
## Current reviewer considerations

Source SHA-256: `6b48b50cfbabd0a320318c122f6c77f8b90e8de052e20cfa2e622eab6bdeae02`.

# Design decisions for `bab4d8f5ba7a`

## Decision standard

A training dimension is retained only when it is lawful, observable in the returned input, honored exactly when overridden, and useful for distinguishing the canonical rule from a plausible wrong rule. Negative probes remain tests rather than ordinary training examples.

## 1. Keep the canonical Racket authority unchanged

**Choice.** Preserve the canonical program and examples; add `RULE_HASH = "1130750019d1"` to the generator.

**Original rationale.** The existing rule text was already synchronized across canonical and base authorities and solved all canonical pairs. The missing generator hash was an integration defect, not evidence that the rule was wrong.

**Alternatives considered.** Rewrite or reformat the Racket source; replace it with the Python mirror; modify canonical examples to cover edge cases.

**Probe.** Authority sync found one exact selected group and execution parity PASS. Racket rule-smoke matched the Python mirror on 120 generated inputs.

**Failure mode / limitation.** Any later authority edit requires updating `RULE_HASH` and rerunning both canonical and generated parity. The Python mirror is test support, not the source of labels.

## 2. Replace independent numeric dimensions with exact scene profiles

**Choice.** Use six named `scene_profile` values whose `(height, width, active rows)` triples are exact: the three canonical geometries plus compact and two larger generalizations.

**Original rationale.** Independent `grid_h`, `grid_w`, and `active_rows` were likely intended to create scale variation. Their declared domains, however, contradicted difficulty-specific draw ranges, and fixed degenerate textures ignored them entirely. The exact original domain rationale was not recorded.

**Alternatives considered.** Keep all three integer axes and enumerate incompatibilities; clamp invalid requests; silently narrow domains by difficulty.

**Why rejected.** Clamping makes an override lie. Difficulty-dependent validity makes the advertised contract unstable. Enumerating every row/height incompatibility adds complexity without creating a more useful learning signal.

**Probe.** The override gate accepted 7,020 draws with no mismatch or rejection. `observe_overrides()` recovers the profile from dimensions and active-row count.

**Failure mode / limitation.** The generator no longer offers every intermediate shape. That is deliberate: six exact, supported profiles are more useful than a broad but false domain.

## 3. Make palette modes structural, not cosmetic metadata

**Choice.** Use three column-zero patterns: all-distinct canonical colors `1..7`, a set guaranteed to include `9`, and a repeated pair.

**Original rationale.** `palette_kind`, `n_distinct_colors`, and `palette_size` appear to have been intended to vary colors. In version 2.1.1, the generator ignored those choices and sampled headers from one fixed set. `palette_size=8` was a singleton and `n_distinct_colors` had no draw provenance.

**Alternatives considered.** Delete palette variation entirely; keep a raw `n_distinct_colors` integer; create warm/cool labels.

**Why chosen.** The three modes are visible and exactly inferable. They test whether the learner follows row-local headers instead of memorizing a unique-color or fixed-palette prior.

**Probe.** Focused tests force every palette value; the override observer recovers each exactly. The strict override gate reports no findings.

**Failure mode / limitation.** The repeated-pair profile weakens the visual cue that every row has a unique header, but the row-local rule remains unambiguous because each row carries its own key.

## 4. Replace random branch occurrence with a five-step teaching schedule

**Choice.** Cycle `canonical_single`, `multi_marker`, `stray_marker`, `mixed_markers`, and `inert_distractors` by `sample_index`, with a small difficulty-dependent phase shift.

**Original rationale.** The version 2.1.1 comments explicitly say that 1–3 markers and occasional stray markers were introduced to exercise “recolor all” and the zero-header skip branch. That rationale is sound, but random occurrence did not guarantee that a lesson or shard would contain the needed counterexamples.

**Alternatives considered.** Independent random probabilities; one giant example containing every feature; separate difficulty-only profiles.

**Why chosen.** A short deterministic schedule gives reproducible coverage while each individual input remains simple. Separate profiles make the relevant contrast attributable; one overloaded scene would confound the cues.

**Probe.** The semantic census covered 600 draws. All five witnesses fired, and named rival claims were verified on every checked witness. The focused default-schedule test sees all five profiles in five consecutive indices.

**Failure mode / limitation.** A downstream stride-five shard can still select one residue class and destroy the local curriculum. This is a packaging concern and motivates the gate proposed in `QUESTION_ANSWER.md`.

## 5. Keep a canonical anchor floor without making it dominant

**Choice.** Declare `MIN_STRICT_FRAC = 0.04` and weight canonical geometries/palettes commonly enough to retain exact public morphology.

**Original rationale.** The original generator already sampled near the public size range, but did not declare or verify the rate.

**Alternatives considered.** Replay only canonical-like scenes; remove strict anchors and rely entirely on generalized examples; require a much higher floor.

**Why chosen.** The model should regularly see the canonical task shape but also must see counterexamples to shortcuts. A low explicit floor makes both requirements measurable.

**Probe.** Strict semantic gate measured 38/600 strict anchors (6.3%), above the 4% floor. Profile floor found exact support in all difficulty bands.

**Failure mode / limitation.** This is a stochastic lower-bound check over a pinned census, not a mathematical distribution proof.

## 6. Remove identity-only and role-ambiguous degenerates from ordinary generation

**Choice.** Remove `no_headers`, `no_markers`, and `header_is_eight` from `AXES` and generation.

**Original rationale.** They appear to have been intended as branch or robustness probes. The exact rationale was not recorded.

**Alternatives considered.** Retain them with explicit incompatibility declarations; put them in a low-probability “hard” branch.

**Why rejected.** `no_headers` and `no_markers` are identity-only and do not teach the transformation. `header_is_eight` conflates the role of the header and marker. All three bypassed normal axis handling and generated thousands of override mismatches.

**Probe.** Final rule-smoke has zero identity outputs in 120 applications. The strict defect lint has zero findings.

**Failure mode / limitation.** These cases may still be valuable as never-train negative fixtures, but they should not be labeled as normal curriculum modes.

## 7. Validate the complete grammar, not mere non-emptiness

**Choice.** Add a pure `analyze_grid()` and make `self_check()` require a declared scene, palette, and teaching profile, at least three active rows, a headerless row, legal headers, at least two header colors, and markers in every active row.

**Original rationale.** The previous self-check only checked dimensions and then accepted blank or markerless grids as “degenerate.” It was acceptance-only: 0/59 generic mutations were rejected.

**Alternatives considered.** Check only row/column bounds; compare generated inputs against the output rule; special-case canonical examples separately.

**Why chosen.** The same structural analyzer supports validation, observability, semantic witnesses, and diagnostics. Canonical inputs are included in the declared profile set, so they need no bypass.

**Probe.** Final self-check accepts 60/60 defaults and 3/3 canonical inputs, while rejecting 50/57 generic destructive mutations. Focused tests explicitly reject blank, markerless, and cyan-header scenes.

**Failure mode / limitation.** Some generic mutations preserve the full lawful grammar and are correctly accepted; mutation rejection is evidence of sensitivity, not a requirement to reject every changed grid.

## 8. Make override truth self-enforcing

**Choice.** Reject unknown keys, expose `observe_overrides()`, record every keyed draw, and compare requested versus observed values inside `generate()` before returning.

**Original rationale.** The generic `**overrides` interface was convenient, but version 2.1.1 silently swallowed typos and declared axes it never drew.

**Alternatives considered.** Rely only on the repository override gate; accept unknown keys for forward compatibility.

**Why chosen.** A local assertion catches drift at the source, while the external gate independently verifies it. Silent forward compatibility is unsafe for training configuration because a typo can appear to succeed.

**Probe.** Unknown-key focused test fails before the rewrite and passes after it. Final override gate reports `unknown_key_verdict: rejected`, zero findings, and zero warnings.

**Failure mode / limitation.** Adding a new override requires updating both `AXES` and the observer; this is intentional friction.

## 9. Declare semantic rivals and bind witnesses to them

**Choice.** Implement four wrong rules and map every semantic witness to at least one rival. Explicitly mark the three wrong rules that are answer-equivalent on the public examples.

**Original rationale.** No semantic contract existed. Surface branch labels alone would not establish that a generated example actually distinguishes the intended rule.

**Alternatives considered.** Positive witness predicates only; natural-language claims; compare only against identity.

**Why chosen.** A witness is useful only when it falsifies a concrete competing hypothesis. Executable rivals make the claim reproducible and protect against witnesses that fire but do not change the answer.

**Probe.** A test was written first and failed because `WITNESS_RIVALS` did not exist. After implementation, 9 focused tests pass and the strict semantic gate verifies all 5 rival claims. It also confirms counterexamples for all three public-equivalent shortcuts.

**Failure mode / limitation.** The rival set is intentionally small and human-chosen. New model errors may require adding new rivals.

## 10. Keep difficulty as weighting, not legality

**Choice.** Difficulty changes the frequency of scene and palette values and shifts the teaching cycle, but every declared override remains legal in every band.

**Original rationale.** The old implementation used difficulty-specific integer ranges, probably to control scale. That made the global axis domain false in easy and hard modes.

**Alternatives considered.** Separate per-band axis schemas; reject cross-band values.

**Why chosen.** One stable contract is easier to test, configure, and reason about. Frequency is sufficient for difficulty shaping here because the rule itself is simple.

**Probe.** The override gate sweeps all cases across easy, medium, and hard with zero explicit rejection.

**Failure mode / limitation.** “Hard” is only distributional complexity, not a guarantee that every hard sample is more difficult than every easy sample.
