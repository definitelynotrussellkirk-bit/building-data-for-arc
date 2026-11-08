# Working notes: 85e65da9fb15

Review `review-ad0b08ee55b0c2ce` found that v2.0.1 pinned the correct authority hash but encoded the wrong task: filled rectangles sorted by area. No prior return was used as a lead; `evidence/associated_notes.jsonl` was empty.

v3.0.0 preserves Racket authority `d63ea92287a9` and replaces the distribution with arbitrary 4-connected shapes assigned in top-left order to the tightest unused fitting frame, preserving orientation when possible, otherwise rotating clockwise, then centering. Three consecutive schedule profiles expose slack/centering, assignment competition, and required rotation with distractors.

Final generator SHA-256: `03e60e7208b6e286645bce4d0abbd63b081c17348db1197762c72c0a1dea9650` before this notes-only edit; generator bytes themselves were not changed by documentation. Final battery: 12/12 green. Portable task tests: 51 passed. Production census: 300 lessons, zero ambiguity, 1,199 unique inputs. Independent probe: 600 distinct draws, no validator/nondeterminism failures, 36 Racket parity cases.

Reusable tooling is in `workspace/reference_probe.py`; regression tests are in `tests/test_generator.py`. Finite shape/rival coverage is not a universal identifiability proof, and catalog approval remains unverified.
## Current reviewer considerations

Source SHA-256: `03e60e7208b6e286645bce4d0abbd63b081c17348db1197762c72c0a1dea9650`.

# Decisions — `85e65da9fb15`

## D1 — Preserve the selected Racket authority

**Choice.** Leave the canonical row and Racket rule unchanged; pin `RULE_HASH = "d63ea92287a9"`.

**Original rationale.** The baseline comment claimed it was written against this hash, but its English summary and generator implemented a different area-sorting rule. No prior return or associated note supplied a justification for changing authority.

**Alternatives considered.** Rewriting authority to match the baseline rectangles would have made existing code pass while contradicting all canonical examples. Editing both generator and rule would also erase the distinction between a source defect and a label defect.

**Probe.** The existing rule reproduces all canonical outputs; authority-sync and rule-smoke pass. The independent Python geometry oracle agrees with the Racket authority on all canonical pairs and 36 generated inputs.

**Failure mode / limitation.** The independent oracle is diagnostic, not label authority. Any future Racket change requires a new hash and a fresh parity run.

## D2 — Replace rectangle/area sorting with the actual sequential assignment law

**Choice.** Generate arbitrary 4-connected shapes, sort loose components by top-left, and assign each to the tightest unused fitting frame with conditional clockwise rotation and centered placement.

**Original rationale.** Baseline v2.0.1 constrained solids to filled rectangles and sorted both solids and frames by area. That rationale appears to have been inferred from a superficial subset rather than the canonical program; canonical shapes are irregular, and assignment is sequential.

**Alternatives considered.** Keeping filled rectangles and only changing the pairing order would still fail to teach component-shape preservation and rotation. Building a generic random packing engine was unnecessary and would make constructive validity harder to guarantee.

**Probe.** Canonical pairs now pass `self_check`; task tests cover irregular polyominoes, tightest-frame selection, top-left processing, centering, rotation preference, and unmatched deletion.

**Failure mode / limitation.** The shape library is finite. It demonstrates the law but is not an exhaustive sampler of all connected polyominoes.

## D3 — Use a deterministic three-profile schedule

**Choice.** Set `EXAMPLES_NEEDED = 3` and rotate `centered_slack`, `order_competition`, and `rotation_distractor` by `sample_index % 3`.

**Original rationale.** The baseline had no executable lesson-identifiability design; its random scenes could not expose the true branches because the domain itself encoded a rival rule.

**Alternatives considered.** Randomly choosing profiles risks three-example lessons missing a critical branch. Packing every branch into every grid makes scenes denser and less legible. A longer schedule increases sample cost without adding a required semantic distinction.

**Probe.** Every three consecutive examples contain all profiles. The source-bound census tested 100 lessons per band and all 300 refuted every declared rival.

**Failure mode / limitation.** A learner may exploit the schedule position itself. The transformation still has to be recovered to solve the varied grids, but future work could randomize profile order while retaining a covering design if the lesson builder exposes a schedule permutation key.

## D4 — Center canonical support in the production distribution

**Choice.** Sample square sizes 12–18 by default, favoring canonical 12–15 sizes, and use canonical palette cardinalities for exact square profiles.

**Original rationale.** Baseline dimensions were 11–14 by 14–17 and never matched the canonical square profiles sufficiently; profile-floor failed.

**Alternatives considered.** An opt-out would hide a correctable distribution gap. Sampling only the four canonical profiles would satisfy the floor but reduce translation and canvas variation.

**Probe.** Profile-floor passes in every band. The independent 600-draw census includes every exact canonical profile and larger 16–18 profiles.

**Failure mode / limitation.** The default square coupling is a deliberate simplification; rectangular 12–18 grids remain available through exact overrides and are tested.

## D5 — Advertise only truthful exact axes

**Choice.** Expose `grid_h` and `grid_w`; reject unknown, non-integer, and out-of-range overrides.

**Original rationale.** Legacy axes named palette, texture, density, and color counts but were not all keyed, observable, or compatible. The before override report contained thousands of mismatches and generation errors.

**Alternatives considered.** Retaining decorative axes would preserve API breadth at the cost of false contracts. Adding exact controls for every internal choice would enlarge the matrix without improving lesson semantics.

**Probe.** The final override stage is green with zero finding or warning categories; unknown keys are rejected. Tests check dimensions and invalid combinations.

**Failure mode / limitation.** Palette and profile selection remain deterministic internal variation rather than user controls.

## D6 — Vary object count without losing witnesses

**Choice.** Use two assigned shapes plus zero, one, or two unmatched distractors, yielding four to six foreground components and five- or seven-color canonical profiles.

**Original rationale.** The first repair draft always emitted six components, which defect-lint correctly identified as outside the canonical median of four.

**Alternatives considered.** Always four components would match the minimum but weaken unmatched-shape deletion. Always six preserves distractors but overconstrains object count.

**Probe.** A regression test first observed `{6}` only; after the change, default sampling includes canonical four-component scenes. Defect-lint then passed.

**Failure mode / limitation.** Exactly two frames remain fixed because the selected teaching design focuses on one-to-one frame use and competition between two slots.

## D7 — Add independent tooling rather than relying on generator internals

**Choice.** Add `workspace/reference_probe.py` with its own component parser, authority mirror, shortcut implementations, sampler census, and optional real-Racket batch parity.

**Original rationale.** No prior workspace tool existed. Using generator helpers alone could make a shared bug appear as agreement.

**Alternatives considered.** Tests could duplicate tiny assertions, but that would not provide a reusable audit artifact or source-bound sampling report. Calling private runner functions directly from reports would be brittle; the probe confines runtime integration to a reproducible tool.

**Probe.** 600 deterministic draws had zero `self_check` errors or nondeterminism, all three canonical shortcuts fit every canonical pair, and 36 generated/canonical inputs matched Racket exactly.

**Failure mode / limitation.** The tool checks declared rivals and sampled grids, not every possible input.

## D8 — Preserve failed evidence and stop after a stable, replayable repair

**Choice.** Keep the baseline battery, first focused-gate failures, full final battery, shortcut witness, solve record, and unrelated audit evidence.

**Original rationale.** There was no prior return used as a lead; `associated_notes.jsonl` was empty. The current packet was treated as the only baseline.

**Alternatives considered.** Deleting intermediate failures would make the fix harder to audit. Continuing to add random shape families after all gates and rival checks passed would increase surface area without a measured defect.

**Probe.** Final source hash is consistent across the after battery, task-test runtime, independent probe, lesson census, and post-repair solve.

**Failure mode / limitation.** Passing checks do not change catalog approval; hidden maintainer scoring may still reveal an undeclared rival.
