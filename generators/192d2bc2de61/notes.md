# Working notes: 192d2bc2de61

## Review 2026-10-07 — assignment `review-098c34d6f9e4cd63`

### Baseline

The selected `3.1.0` sampler assumed a contiguous row-0 prefix and generated only one body component per legend color. Its validator rejected all five canonical inputs because the canonical legends may be sparse or offset. The source also omitted the canonical `RULE_HASH`, advertised non-exact/dead controls, had no executable semantic contract, and did not cover canonical object counts. The retained before battery (`checks/before/`) finished with 6 green stages, 1 advisory stage, and 5 failed stages.

The strongest canonical-compatible shortcut was “choose the first/top-left component of each legend color.” It fits all five canonical pairs because each canonical color has one body component. A source-bound generated counterexample is retained at `checks/shortcut-witness-generated/`: seed `4242`, sample index `0`, difficulty `easy`, profile `spaced_10x14`. The selected Racket output differs from the shortcut output and matches the task-local intended mirror.

### Repair

Version `4.0.0` keeps the Racket rule unchanged and replaces the old controls with one exact `scene_profile` axis:

- `prefix_10x13`: canonical-core single-component support;
- `spaced_10x14`: sparse legend plus one earlier same-color decoy per color;
- `offset_11x14`: shifted sparse legend plus two decoys per color;
- `wide_11x15`: wider sparse legend plus two decoys per color.

Each profile has three distinct legend colors, a blank separator row, uniquely largest body components, and a deranged body placement. The diagnostic profiles therefore make the canonical-fitting first-component shortcut fail, while all profiles make body-order packing fail. Exact overrides, malformed inputs, canonical acceptance, independent canonical outputs, canonical shortcut fit, semantic witnesses, lesson competitors, and nonmutation are covered by task-local tests.

### Verification

Final generator SHA-256: `08607a3107398b9288cca6544f93a090188550f83ad81b13220a88570617e393`.

- Final 12-stage battery: 12/12 green (`checks/after/checks/192d2bc2de61_after_battery_summary.json`).
- Task-local tests: 36/36 pass (`checks/task-tests/checks/task_tests.xml`; rerun after adding the workspace probe).
- Required query-rotation semantic gate: pass (`checks/required-rotations/`).
- Shared lesson census: 300/300 lessons materialized, 900 labelled pairs, 900/900 query rotations, 900 unique inputs, zero ambiguous lessons/rotations, hook warnings, hook errors, or scoring errors against the declared rivals (`checks/lesson-census.json`).
- Independent probe: all exact profiles and declared shortcuts checked; 192 cyclic query rotations passed, with zero failures (`checks/review-probe.json`).
- Post-repair visible-only solve: one revision, 3/3 visible examples; earlier rule exposure declared `yes`, reference consulted during solve declared `no` (`solve/summary.json`).

### Retained failed iterations

- `checks/after-attempt1/`: static lint rejected a nonliteral `AXES` declaration; defect lint also found byte-identical difficulty bands and missing canonical object-count support.
- `checks/after-attempt2/`: only canonical object-count support remained; adding the canonical-core profile resolved it.
- Red-first test logs are retained in `checks/test-red.log`, `checks/test-band-red.log`, and `checks/test-canonical-count-red.log`.

### Limits

The semantic evidence is finite and only covers the declared rivals plus the explicit first-component witness. The curriculum is deliberately structured around a four-profile period, although the retained rotation checks support arbitrary held-out query position within the tested lessons. All ordinary scenes use exactly three legend colors and canonical canvas/palette cardinality; broader color-count generalization was not claimed. Catalog approval and train-safety remain maintainer decisions.
## Current reviewer considerations

Source SHA-256: `08607a3107398b9288cca6544f93a090188550f83ad81b13220a88570617e393`.

# Decisions for `192d2bc2de61`

Final generator SHA-256: `08607a3107398b9288cca6544f93a090188550f83ad81b13220a88570617e393`
Canonical rule hash: `5ea0808c0383`

## D1 — Preserve the selected Racket authority

**Choice.** Leave the Racket rule unchanged and pin the Python generator to `RULE_HASH = "5ea0808c0383"`.

**Rationale.** The canonical examples, rule-smoke checks, and independent Python interpretation all agree: read nonzero row-0 legend colors left-to-right, select the largest four-connected body component for each color, crop, and pack with one-column gaps. The failures were in the sampler, validator, and teaching distribution rather than the rule.

**Alternatives considered.** Narrowing the Racket rule to a contiguous legend prefix would have matched the baseline sampler but contradicted canonical sparse/offset legends. Changing tie behavior was unnecessary because lawful generated scenes have a unique largest component.

**Probe / failure mode.** Authority sync and rule smoke are green in the final battery. Any later rule edit must update the pin and rerun canonical parity; this return supplies no justification for such an edit.

## D2 — Replace pseudo-axes with one exact `scene_profile` control

**Choice.** Advertise only `scene_profile`, with four literal values and exact pixel-observable meanings.

**Original rationale.** Unknown. The imported baseline advertised controls that did not form a reliable exact contract and mixed implementation details with semantic variation.

**Alternatives considered.** Independent height, width, legend-spacing, decoy-count, component-size, and position axes would create a large joint override surface and many incompatible combinations. A profile axis is sufficient for the four necessary semantic contrasts and is exhaustively testable.

**Probe / failure mode.** Every profile override is tested under `None`, easy, medium, and hard; unknown or malformed values fail loudly. The override gate passes. The trade-off is less combinatorial freedom, explicitly accepted in favor of an honest contract.

## D3 — Match canonical canvas/palette support exactly

**Choice.** Use only 10×13, 10×14, 11×14, and 11×15 scenes with background plus three distinct nonzero colors.

**Rationale.** These are the measured canonical profiles. The baseline validator rejected all canonical inputs and failed profile-floor checks. Exact canonical-sized support avoids teaching a size or palette-count shortcut.

**Alternatives considered.** Keep broader 9–12 by 13–16 ranges and hope strict-profile draws occur randomly. This failed the profile floor and made exact override behavior harder to explain.

**Probe / failure mode.** `strict_canonical_like` accepts every generated draw and all five canonical inputs; the final distribution report measured 600/600 strict hits across the three bands. The generator does not claim generalization to other canvas sizes or color counts.

## D4 — Include one canonical-core profile without decoys

**Choice.** `prefix_10x13` contains exactly one body component per legend color.

**Rationale.** The first two repair attempts generated 9–12 components in every scene, while canonical inputs have a median object count of six. Defect lint correctly flagged that the real distribution was unreachable. One no-decoy profile restores canonical-core object-count support.

**Alternatives considered.** Reduce all profiles to one component per color. That would reintroduce the strongest canonical shortcut and fail to teach “largest.” Reduce decoys probabilistically. That would make lesson support nondeterministic.

**Probe / failure mode.** The task test `test_prefix_profile_reaches_canonical_single_component_count` was written red first and then passed; final defect lint is green. Because this profile alone does not refute `first_component`, the linked schedule must retain diagnostic profiles.

## D5 — Add earlier same-color decoys in the three diagnostic profiles

**Choice.** Place one or two singleton decoys above each uniquely larger main component.

**Rationale.** “Choose the first/top-left component” fits 5/5 canonical pairs. Earlier singleton decoys make that shortcut visibly wrong while leaving the intended answer unambiguous.

**Alternatives considered.** Same-size competitors would exercise tie-breaking but could obscure the central lesson and make output sensitive to authority tie details. Larger decoys below the main object would not refute a top-left shortcut. Random decoy presence would weaken every-window guarantees.

**Probe / failure mode.** The generated witness at `checks/shortcut-witness-generated/` passes `self_check`, fires the witness, and produces different Racket and rival outputs. Three of four profiles guarantee this contrast. Ties remain outside the ordinary generated domain.

## D6 — Derange body spatial order from legend order

**Choice.** Place the three main components in one of four derangements of the body slots.

**Rationale.** Without this contrast, a solver could ignore the legend order and pack components left-to-right by location. The legend should control output order.

**Alternatives considered.** Random permutations including the identity would create lessons where the shortcut survives. A fixed single derangement would be semantically sufficient but less diverse.

**Probe / failure mode.** The `body_order` rival is declared and checked in every lesson. The census refuted it in all 100 lessons per band. Spatial order is only varied among three fixed slots; more general layouts remain untested.

## D7 — Teach sparse and offset legend parsing

**Choice.** Include contiguous, zero-spaced, and leading-zero row-0 legends.

**Rationale.** The selected authority reads every nonzero row-0 cell, and canonical inputs include sparse/offset layouts. The baseline’s contiguous-prefix assumption was the direct canonical rejection cause.

**Alternatives considered.** Keep a contiguous prefix and merely relax `self_check`. That would accept canonical inputs without actually teaching the canonical parsing rule.

**Probe / failure mode.** `prefix_legend` is an executable rival; sparse/offset profiles refute it. Canonical and generated inputs are checked by the task tests and semantic gates.

## D8 — Use a deterministic four-profile curriculum with band phase offsets

**Choice.** Cycle profiles by sample index and phase-shift medium/hard schedules.

**Rationale.** Determinism makes support auditable. Any two-demonstration window plus query contains sufficient contrast under the tested cyclic policy, and band offsets avoid byte-identical difficulty distributions.

**Alternatives considered.** Independent random profile choice could produce all-core lessons that fail to teach largest-component selection. Identical schedules across bands triggered a retained defect-lint warning.

**Probe / failure mode.** All cyclic starts and query positions were checked by `review_probe.py`; the shared census covered 100 starts per band and 900 rotations. The schedule is structured and should not be silently replaced by independent sampling without rerunning identifiability checks.

## D9 — Declare executable mirrors, witnesses, shortcuts, and competitors

**Choice.** Add pure deterministic solvers for intended behavior, `first_component`, `prefix_legend`, and `body_order`; bind witnesses to the rivals they are meant to refute.

**Rationale.** Narrative claims are not enough to establish that generated lessons teach the rule. The canonical shortcut must be shown to fit the canonical pairs, then be shown to fail on generated demonstrations.

**Alternatives considered.** Static metadata only, or tests that copy rival names. Those can drift from production declarations. The workspace probe imports the actual dictionaries instead.

**Probe / failure mode.** Canonical fit, witness disagreement, lesson survival, purity, and rotation behavior are retained in the task tests, census, and probe. These rivals are finite and do not exhaust all hypotheses.

## D10 — Require rotation evidence for the claimed lesson policy

**Choice.** Claim held-out query flexibility only because the required-rotation gate and the 300-lesson census were run with every labelled pair held out once.

**Rationale.** Correct ordered lessons do not automatically imply arbitrary query placement. Downstream assembly may rotate the query, so the claim needed direct evidence.

**Alternatives considered.** Declare an ordered-only curriculum and use diagnostic rotations. That would be defensible but unnecessarily restrictive after the final distribution passed required rotations.

**Probe / failure mode.** The required semantic stage passed; 900/900 census rotations had zero ambiguity against declared rivals. This remains finite evidence and does not enumerate every possible seed or undeclared rival.

## D11 — Build a reusable reviewer probe

**Choice.** Add `generators/192d2bc2de61/workspace/review_probe.py` and document it in the workspace README.

**Rationale.** Future agents need one command that verifies source identity, actual declaration dictionaries, exact profiles, canonical shortcut fit, cyclic starts, query rotations, and uniqueness.

**Alternatives considered.** Rely only on one-time logs. Those are valuable evidence but less useful for later source revisions.

**Probe / failure mode.** The final run covered 192 cyclic rotations and 100 uniqueness draws with zero failures. It is a task-local supplement; Racket-backed shared gates remain authoritative.

## D12 — Leave audit targets unchanged

**Choice.** Report the `102e79f0ca6d` defect and the negative `dadeacb21d08` audit without editing either target.

**Rationale.** Assignment step 7 is findings-only and selected-task edits should remain isolated.

**Probe / failure mode.** The 102 reproducer is an ordinary default sample and includes Racket output. The dade audit covered all 192 boundary combinations, 300 ordinary draws, 300 lessons, and 64 Racket parity cases; “No issue found” is limited to those checks.
