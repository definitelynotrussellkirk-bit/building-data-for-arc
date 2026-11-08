# Working notes: 786a759f780e

## Review identity

- Assignment: `review-0510afbf03a90f32`.
- Selected baseline generator SHA-256: `f39d892dcc44fcfe656bfb763121029c92be20bd5d3b3f483fecceb8c14ba644`.
- Final generator SHA-256: `e5caaeb59dcbcfd5c9efc45b2d8291e96d7ce8600302237107dd80e8136ce7ba`.
- Canonical rule hash: `71abd31a186f`; the Racket authority was not changed.
- Prior return used only as an investigation lead: `review-d9ccd3d6d96df1a5:v0001`, recorded in `evidence/review_index.json`. Its 0/300-hole observation was reproduced conceptually against the selected baseline before repair rather than accepted as a current measurement.

## Baseline defect and root cause

The baseline described a vertical gallery of per-color 3–5-cell random-walk motifs. The authoritative rule instead finds all-nonzero 4-connected components, permits colors to mix inside a component, counts holes, sorts by `(holes, area, key color)`, and packs horizontally. A 3–5-cell 4-connected polyomino cannot contain the one-cell enclosure needed to vary the primary sort key, so the baseline distribution could not teach hole-first ordering at all. It also lacked a pinned `RULE_HASH`, advertised ineffective controls, accepted structural impostors, and supplied no executable semantic rivals.

The retained before battery is `checks/before/checks/786a759f780e_before_battery_summary.json`: 7 green, 2 advisory, and 3 failed stages (`lint`, `defect_lint`, `override`). The test-first reproduction is `checks/tdd-red/result.json`: 15 failed, 1 passed.

## Selected design

### Teaching profiles

A deterministic three-residue `C/H/T` schedule drives five-example lessons:

1. `canonical_holes` anchors the public morphology with 0-, 1-, and 2-hole objects.
2. `hole_priority` uses areas 12, 8, and 13 for 0-, 1-, and 2-hole objects, forcing the primary hole key to beat area-only ordering.
3. `tie_chain` gives all objects one hole, two equal-area rings with different key colors, and a larger ring. It exposes area ascending and then color ascending.

Every sliding five-sample window, and every leave-one-out rotation of a six-pair lesson, contains all three profiles. Input slot permutations always disagree with answer order. Every ordinary draw recolors one non-key cell in one component, making per-color extraction observably wrong while preserving component connectivity and the key color.

### Grammar and controls

The grammar is intentionally narrow enough for reliable teaching: three linked profile morphologies, two canonical canvas sizes, exactly three foreground colors, separated components, and non-identity packing. `self_check` recognizes linked morphology rather than merely bounding dimensions. `strict_canonical_like` uses exact public joint signatures, including the two-component canonical examples. Unknown axes and out-of-domain values fail loudly. `observe_overrides` makes both exact controls measurable.

### Semantic contract

The generator exposes independent executable competitors for:

- area-only ordering;
- hole-only ordering;
- area descending;
- missing the color tie-break;
- reading-order packing;
- color-order packing; and
- same-color component extraction.

`CANONICAL_SHORTCUTS` is limited to rivals that actually fit every usable canonical pair. `LESSON_COMPETITORS` and `lesson_identifiable` test complete demonstrations against differing queries rather than only counting individual witnesses.

## Verification

- Final battery: `checks/after/checks/786a759f780e_after_battery_summary.json`, 12/12 green.
- Final task-local regressions: `checks/task-tests/result.json`, 16/16 passed.
- Independent oracle/census tool: `workspace/reference_probe.py`; retained output `checks/reference-probe.json`. For each difficulty band, 60/60 inputs were unique, 60/60 had a mixed component, the profile count was exactly 20/20/20, 20/60 were strict canonical hits, deterministic replay held, and every declared rival was refuted by its intended profile.
- Production source-bound census: `checks/lesson-census.json`, 300/300 lessons materialized, 1,800 labelled pairs, 1,800 query rotations, 1,694 unique inputs, zero declared-rival ambiguities, zero hook warnings, and zero scoring errors.
- Post-repair visible-only solve: `solve/summary.json`, one genuine revision passed all five visible examples and is bound to the final generator hash.

## Known limits and next work

The profile silhouettes are deliberately structured and only vary by reflection, color, mixed-cell placement, canvas, and spatial arrangement. This strongly separates the declared rivals but does not prove that no undeclared silhouette-memorization rule fits the finite lesson family. A later expansion could add multiple topology-preserving shape families per profile while retaining the same C/H/T guarantees and exact semantic tests. The finite rival census is evidence against declared competitors, not a proof of universal identifiability.
## Current reviewer considerations

Source SHA-256: `e5caaeb59dcbcfd5c9efc45b2d8291e96d7ce8600302237107dd80e8136ce7ba`.

# Decisions: 786a759f780e

## D1 — Treat the selected baseline as untrusted and reproduce the defect

**Choice.** I used prior return `review-d9ccd3d6d96df1a5:v0001` only as a lead, then inspected and checked the pinned baseline with SHA-256 `f39d892dcc44fcfe656bfb763121029c92be20bd5d3b3f483fecceb8c14ba644`.

**Reason.** The assignment explicitly distinguishes prior claims from measurements of the selected source. The baseline's 3–5-cell random-walk domain makes a one-cell hole structurally impossible, which explains the mismatch rather than merely correlating with it.

**Probe.** The before battery and a test-first suite are retained under `checks/before/` and `checks/tdd-red/`.

## D2 — Preserve the Racket authority

**Choice.** Pin `RULE_HASH="71abd31a186f"` and repair only the Python generator, tests, and task workspace documentation/tooling.

**Reason.** The canonical Racket program consistently solves all five public pairs. The defect was distributional and descriptive, not an incorrect authority.

**Rejected alternative.** Rewriting the Racket rule to match the old vertical-gallery generator would have changed the task and contradicted canonical outputs.

## D3 — Use a deterministic three-profile curriculum

**Choice.** Schedule `canonical_holes`, `hole_priority`, and `tie_chain` by `sample_index mod 3`; set `EXAMPLES_NEEDED=5`.

**Reason.** Each profile has one semantic job, and every contiguous five-example window contains every profile. A six-pair materialized lesson also remains covered under every leave-one-out query rotation. This gives a simple invariant that tests can exhaust over all cyclic starts rather than relying on witness frequency.

**Rejected alternatives.** Pure random profile selection can produce complete lessons missing a critical contrast. Rejection-sampling an assembled lesson would be more complex, obscure accepted indices, and make replay/debugging harder.

## D4 — Construct explicit contrastive morphologies

**Choice.** Use linked masks with known hole/area facts:

- canonical: `(holes, area) = (0,4), (1,8), (2,23)`;
- hole-priority: `(0,12), (1,8), (2,13)`;
- tie-chain: `(1,8), (1,8), (1,12)` with distinct first colors on the equal-area pair.

**Reason.** These values make the sort-key precedence observable. A random shape generator could satisfy broad ranges while rarely or never creating the exact conflicts needed to refute plausible shortcuts.

**Rejected alternative.** Generating arbitrary hole-bearing polyominoes would improve morphology variety but needs a much larger constructive/validation surface to guarantee each lesson's contrasts. It is a sensible future extension after retaining the current semantic tests.

## D5 — Make connectivity semantics visible

**Choice.** Recolor one non-key cell inside one component on every ordinary draw.

**Reason.** The authority groups all nonzero cells, not cells of equal color. Without a mixed component, a same-color connected-component rival is observationally equivalent on the entire lesson.

**Failure mode considered.** Recoloring the first row-major cell could silently alter the final sort key. The implementation recolors the last painted cell and independently checks the mirror against the oracle.

## D6 — Deliberately conflict input and output order

**Choice.** Place profile roles into three separated slots through non-identity permutations; `tie_chain` additionally puts the high-color equal-area ring before the low-color ring in reading order.

**Reason.** This defeats both reading-order packing and omission of the final color tie-break.

**Rejected alternative.** Uniformly random placements can accidentally place objects in correct output order, weakening complete lessons even when aggregate diversity is high.

## D7 — Keep only exact, observable overrides

**Choice.** Advertise `scene_profile` and `canvas_profile`; reject unknown keys and invalid values; expose `observe_overrides` and validate requested versus observed values in `self_check`.

**Reason.** Controls should be contractual, not hints accepted and ignored. The two axes are independently testable and cover the useful authoring choices.

**Rejected alternative.** Fine-grained color, reflection, and layout overrides would increase contract combinations without improving production training quality.

## D8 — Validate linked structure, not only dimensions

**Choice.** `self_check` recognizes one of the three intended morphologies, exact palette cardinality, separation, and non-identity transformation. `strict_canonical_like` uses exact linked public signatures and accepts all five canonical examples, including two-component cases.

**Reason.** The old validator accepted structural impostors. Stronger validation protects both generated data and overrides from silently drifting outside the declared grammar.

## D9 — Declare executable rivals and test whole lessons

**Choice.** Add `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, `semantic_signature`, and `lesson_identifiable`.

**Reason.** Correct labels and per-draw witness counts do not prove that demonstrations distinguish the intended rule on the query. Whole-lesson tests require a rival to fit every demonstration and then compare its query prediction.

**Probe.** `workspace/reference_probe.py` implements an independent oracle. The shared source-bound census checked 300 production lessons and 1,800 rotations with no declared-rival ambiguity.

## D10 — Preserve a narrow but honest scope

**Choice.** Keep two canonical canvas sizes, three components for generated profiles, and limited topology templates, while documenting the limitation.

**Reason.** This repair prioritizes guaranteed semantic contrasts over unconstrained visual variety. The final census found 1,694 unique inputs among 1,800 labelled pairs, but uniqueness from nuisance variation is not the same as topological variety.

**Known limitation.** An undeclared learner could key on recurring silhouettes. Future work should add several topology-preserving mask families per role while keeping all existing whole-lesson and independent-oracle tests.

## 2026-10-25 native parametric build — assignment `review-61c809e9a3a3127e`

The production generator remains byte-for-byte unchanged at
`e5caaeb59dcbcfd5c9efc45b2d8291e96d7ce8600302237107dd80e8136ce7ba`.
A native family now exposes episode-fixed `hole_order`:

- `ascending` is the exact canonical Racket program (SHA-256
  `47d9603ce1b57c3124c98da91980bfa74990a432166bc40a9d1d3ee58a1a2db2`);
- `descending` reverses only the primary enclosed-hole-count ordering while
  retaining ascending area and first-color tie-breaks.

Inputs are matched across settings and stable under independent 2–6 demo and
1–4 query requests.  The first two demonstrations eliminate the alternate
setting and twelve retained finite shortcuts, including area-only, hole-only,
missing-tie-break, reading-order, color-order, and same-color-component rules.
Four private queries include a substantive 30×30 boundary-spanning scene with
five mixed-color components, 90 foreground cells, and hole counts 0 through 3.

Sequential dependency: Step A extracts each complete nonzero 4-connected
component and derives its exact enclosed-hole count, area, row-major key color,
and crop; Step B consumes those records to sort by the episode policy and pack
the crops.  A qualification-bound counterfactual replaces the derived ordering
with area-only ordering and changes 110 padded output cells.

Retained evidence: 36/36 staged tests; protected self-audit with eight jobs,
130 Racket evaluations and 256 deterministic stress episodes; native
qualification with four jobs/32 labels; 16/16 one-query public projections; and
owner-format causal replay status `owner_replayed`.  Exact-source owner
acceptance and training admission remain separate and were not performed.
