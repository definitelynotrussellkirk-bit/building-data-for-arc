# Working notes: 83efd4fcb4f4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `07c2109338ae2b718e248bee927e6cf45179bcf3a72fe59022e63004e2990099`.

# Decisions — `83efd4fcb4f4`

The baseline's retained notes do not explain most input choices, so “original rationale” below is marked unknown except where the imported summary makes the intent explicit. Finding IDs match `REVIEW.md`.

## D1 — Preserve the Racket authority and pin it explicitly

**Related finding:** R1
**Original rationale:** The imported summary describes the same hollow-plus-center transformation, but the Python module omitted the required authority pin. No rationale for that omission was retained.
**Decision:** Keep the selected Racket rule unchanged and add `RULE_HASH = "a8ddd603c662"`. Keep the Python `rule_mirror` only as an independently testable review hook.
**Alternatives rejected:** Rewriting the authority to match a simplified Python generator; changing canonical examples; treating the missing pin as documentation-only. Those alternatives would hide source drift or expand the repair beyond the measured defect.
**Probe/evidence:** Canonical Python-mirror parity in the task tests; final `rule_smoke`, `racket_lint`, and `authority_sync`; authority-set SHA-256 `154b50d86267f18edf73f5dfa9fa2b99d5e35407bd10e98fcdb890cf5f33333c`.
**Failure modes and limits:** A pinned hash catches authority replacement, not every semantic mistake in the Python mirror. Racket remains the label authority.

## D2 — Replace fictitious axes with three exact observable controls

**Related finding:** R1
**Original rationale:** Unknown. The baseline advertised palette, density, texture, position, and count controls, but several were dead, single-token, degenerate, or not observable.
**Decision:** Advertise only `grid_h` 8–12, `grid_w` 9–13, and `n_targets` 1–5. Reject unknown keys, invalid types, booleans, and out-of-range values. Re-observe every generated grid and require exact equality with requested values.
**Alternatives rejected:** Keeping broad axes as “diagnostic”; silently clamping impossible requests; declaring a long incompatibility table; retaining texture values that deliberately destroy all targets. Those choices would keep unusable controls in training metadata or make accepted overrides untrustworthy.
**Probe/evidence:** Task tests exercise every target count and representative shape in all bands. The final override matrix accepts 8,370/8,370 draws across 93 cases, with zero findings and unknown-key rejection.
**Failure modes and limits:** The contract is deliberately small. Palette and clutter complexity are not externally steerable; adding them later requires real independent support and an observer.

## D3 — Use canonical-scale shape ranges and band-specific deterministic cycles

**Related finding:** R1
**Original rationale:** The baseline summary targeted roughly 8–10 by 9–11, but the defect linter measured canonical object-count coverage outside the generated range. No reason for the narrower range was retained.
**Decision:** Use shapes 8–12 by 9–13. Each difficulty has a five-shape cycle at canonical scale, while exact overrides can choose any legal height/width. The keyed draw still records full-domain provenance; the scheduled value is arranged at the RNG-selected index rather than bypassing `GenCtx`.
**Alternatives rejected:** Fully random dimensions, which can make rare teaching layouts disappear; one fixed shape per band, which would create a stronger metadata shortcut; much larger grids, which add irrelevant empty area and reduce profile construction reliability.
**Probe/evidence:** Profile-floor and distribution gates, 300-draw independent probe, exact override matrix, and deterministic replay tests.
**Failure modes and limits:** Difficulty primarily changes shape/clutter scale rather than rule complexity. The deterministic cycle is visible metadata, so tests must ensure it does not determine outputs independently of local geometry.

## D4 — Default target-count cycle `2, 2, 5, 3, 2`; exact support remains 1–5

**Related finding:** R1
**Original rationale:** The imported summary used 2–3 separated pluses. That was too sparse to reproduce the canonical object-count regime and excluded overlap cases.
**Decision:** Default to `2, 2, 5, 3, 2` across the five teaching profiles. Support 1, 2, 3, 4, and 5 exactly through `n_targets`.
**Alternatives rejected:** Uniform random target count, because it can omit dense and overlap witnesses from a lesson; always five targets, because it narrows visual diversity; forcing every count into the five-example cycle, because the curriculum also needs semantic profile coverage.
**Probe/evidence:** Constructive exact-count tests for every profile and every count; canonical coverage gate; 8,370-draw override check.
**Failure modes and limits:** Default samples do not naturally emit counts 1 or 4; those are contract-supported through overrides. A downstream sampler that never uses overrides sees the scheduled distribution, not a uniform 1–5 distribution.

## D5 — Construct exact plus centers rather than paint-and-hope

**Related finding:** R1
**Original rationale:** The baseline painted sparse separated crosses and accepted degenerate textures; no evidence showed it guaranteed the intended count after overlap or clutter.
**Decision:** Choose candidate centers, paint their cardinal arms, and accept only when `_true_centers(grid)` equals the chosen set exactly. Recheck this invariant after every near-miss and clutter operation. Retry construction up to 256 times with attempt-keyed RNG.
**Alternatives rejected:** Independent random color-3 pixels followed by filtering; counting visual plus objects instead of exact centers; allowing accidental extra targets and changing metadata afterward. Those approaches weaken exact override semantics and can mislabel the task manifold.
**Probe/evidence:** Exact-count/profile tests, `self_check`, `observe_overrides`, independent `plus_probe.py`, and all source-bound battery stages.
**Failure modes and limits:** Constructive retry is bounded. A future combination of tighter shapes, more targets, or more required decoys could exhaust 256 attempts and must be measured rather than silently relaxed.

## D6 — Five semantic profiles with redundant evidence

**Related findings:** R2, R3
**Original rationale:** Unknown; the baseline had no explicit curriculum or lesson contract.
**Decision:** Cycle `sparse`, `shared`, `boundary`, `three_arm`, and `diagonal`. The final implementation duplicates counterevidence so every five-of-six held-out-query rotation still refutes each declared rival. Specifically, diagonal decoys occur in four profiles, three-arm decoys in two, shared-arm configurations occur across multiple profiles, and boundary targets are common.
**Alternatives rejected:** A single random mixture, which gives no per-lesson guarantee; exactly one witness per five examples, which caused the measured 292/1,800 rotation failures; adding more demonstrations, which increases data cost and was unnecessary once evidence was redundant.
**Probe/evidence:** The first source-bound census passed all ordinary lessons but failed 292/1,800 rotations. A failing task-local regression was added before repair. The final task test checks 7,200 local rotations, and the final census checks 1,800 production rotations with zero ambiguity.
**Failure modes and limits:** Redundancy is verified only for the four declared competitors. New plausible rivals may require new profiles or different witness allocation.

## D7 — Declare executable rivals, including the real canonical shortcut

**Related finding:** R2
**Original rationale:** The baseline declared no semantic hooks.
**Decision:** Add four executable rivals: `at_least_three_arms`, `cardinal_or_diagonal`, `separated_targets_only`, and `margin_two_only`. Declare `cardinal_or_diagonal` as a `CANONICAL_SHORTCUT` because it fits every usable canonical pair, and bind each semantic witness to the rival it refutes.
**Alternatives rejected:** Metadata-only rival names; rivals copied only into a probe; claiming canonical examples uniquely determine the rule; adding arbitrary implausible mutations merely to raise a count. Executable rivals let the shared gate verify both claims and lesson behavior.
**Probe/evidence:** Task test proves the diagonal rival fits all five canonical pairs and differs on generated diagonal decoys. Final semantic gate verifies 4/4 rival claims and 4/4 witness types.
**Failure modes and limits:** Rival selection involves judgment. It is not an exhaustive hypothesis class, and a model can still learn a shortcut not represented here.

## D8 — Strict domain validator, but retain all lawful canonical inputs

**Related finding:** R1
**Original rationale:** Unknown. The baseline validator accepted every tested destructive mutation, including blank grids.
**Decision:** Validate nonempty rectangular integer grids, shape range, input palette 0/3/6/7, one to five exact targets, at least four green cells, presence of color 6, exactly two separated color-6/7 components, component sizes 3–4, and component monochromaticity. Return diagnostics rather than raising on malformed grids.
**Alternatives rejected:** Validation based only on shape/palette; requiring every generated profile witness in every individual input; rejecting canonical inputs that do not have generated distractor geometry. The final validator was tuned to the reviewed manifold while explicitly checking canonical acceptance.
**Probe/evidence:** 5/5 canonical inputs accepted; 60/60 sampled defaults clean; 62/68 destructive mutations rejected. The six unrejected duplicate-row mutations remain lawful variants rather than automatically invalid grids.
**Failure modes and limits:** `self_check` validates the input manifold, not lesson identifiability. A valid input can still be a poor teaching example unless curriculum gates are also applied.

## D9 — Exactly two small distractor components in colors 6/7

**Related finding:** R1
**Original rationale:** The imported summary mentioned one or two isolated color-6/7 cells, but canonical examples use richer distractor structure.
**Decision:** Place exactly two separated monochromatic 4-connected components, each a triomino or tetromino of size 3–4. Use color pairs `(6,6)` or `(6,7)` while guaranteeing color 6 appears. Reserve target and decoy centers so distractors cannot corrupt the rule geometry.
**Alternatives rejected:** Isolated single pixels, which underrepresent canonical object scale; arbitrary random blobs, which complicate exact validation; distractors using color 3, which can accidentally create or destroy target evidence.
**Probe/evidence:** Independent probe reports component sizes for every sample; self-check and defect-lint are green; all canonical inputs remain accepted.
**Failure modes and limits:** The distractor grammar is intentionally simple and may be learnable as irrelevant by itself. It tests color/object irrelevance but not every possible clutter topology.

## D10 — Keep the reusable probe independent of production code

**Related findings:** R1–R3
**Original rationale:** No task-local tests or independent probe existed.
**Decision:** Add `workspace/plus_probe.py`, which loads a generator by path but implements its own oracle, target detector, connected-component analysis, witnesses, and rivals. It emits a JSON report suitable for future agents. Add 53 task-local tests under the required `tests/` directory.
**Alternatives rejected:** A probe that imports private helpers from `generator.py`, because the same defect could satisfy both implementation and test; relying only on the shared battery, because selected-task tests are not automatically discovered by generic root pytest; prose-only review notes.
**Probe/evidence:** `checks/plus-probe-final.json` covers 300 draws; task-local tests pass in both working and clean-applied packet runtimes.
**Failure modes and limits:** The probe mirrors a finite interpretation and can itself be wrong. Canonical parity and public Racket checks provide the authority cross-check.

## D11 — Do not modify either adversarial audit target

**Related findings:** A1, A2
**Original rationale:** The assignment explicitly makes audits review-only.
**Decision:** Retain concrete probes, public Racket evidence, and suggested repairs, but leave `generic_dense_motion_gen3` and `39e5f1c25127` unchanged.
**Alternatives rejected:** Bundling opportunistic audit fixes into the selected-task delta; reporting only a suspicion without an authority-bound counterexample.
**Probe/evidence:** `AUDIT.md` and `checks/audits/`.
**Failure modes and limits:** The findings remain unresolved in those target sources until separately assigned.

## D12 — No reference-rule or canonical-data edit

**Related findings:** R1–R3
**Original rationale:** The canonical rule already labels the task correctly; defects were in sampling, contracts, and teaching coverage.
**Decision:** Do not modify `repo/shared/data/canonical/puzzles.jsonl` or base solution banks.
**Alternatives rejected:** Adding a diagonal-decoy canonical example to disambiguate the public task; changing output colors or rule semantics. Those would alter authority rather than improve generated training data.
**Probe/evidence:** Final patch path list contains only the four selected generator/test/workspace files, and final authority synchronization is green.
**Failure modes and limits:** Canonical examples remain ambiguous under the diagonal-X rival in isolation. Generated lessons now supply the missing evidence, but consumers using canonical pairs alone retain that ambiguity.
