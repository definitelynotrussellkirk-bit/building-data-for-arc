# Working notes: 2dae2c34641b

## Baseline diagnosis

- Before battery: 7 green, 2 advisory, 3 failed.
- Missing `RULE_HASH`; selected canonical hash is `95bc32a62544`.
- Nine advertised axes/textures did not match implementation: dead palette textures, duplicated pair/color counts, unprobeable fixed axes, special modes bypassing dimension overrides, and unknown overrides accepted.
- Easy had zero exact canonical-profile hits in 20 draws.
- No semantic contract existed.
- Canonical examples all have exactly two colors, so “process only the first two pairs” fits 5/5 pairs.

## Selected repair

- Version 2.0.0 with exact axes: dimensions, pair count, palette band, and bend pattern.
- Canonical-profile dimensions in every band.
- Three-sample schedule `2,2,3` pairs; palettes `low,mid,high`; bends `left,right,mixed`.
- Strict endpoint grammar and pairwise-disjoint canonical paths.
- Executable `horizontal_first` and `first_two_pairs_only` competitors, witnesses, and `lesson_identifiable`.
- Cached candidate bitmasks and lazy coprime traversal after the first exact override matrix exposed full-pool shuffle cost.

## Final evidence

- Final generator SHA-256: `cadbe43ce6f4cb7bf6df1437f0efbbe1b45270df8fa2d5f55972d5f7dc8e4838`.
- Full after battery: 12/12 green (`checks/after-final/`).
- Exact override matrix: 10,800/10,800 accepted, 0 findings (`checks/override-final/`).
- Task-local tests: 10 passed.
- Racket-backed lesson probe: 300/300 identifiable, 1,200 unique inputs, zero rival survivors (`checks/semantic-lessons/lesson-probe.json`).
- Racket authority unchanged; only the generator and task-local tooling/tests/documentation changed.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `cadbe43ce6f4cb7bf6df1437f0efbbe1b45270df8fa2d5f55972d5f7dc8e4838`.

# Decisions — 2dae2c34641b

The baseline notes did not document the original design rationale, so “original rationale” below is marked unknown where it cannot be recovered from code or evidence.

## D1 — Keep the canonical Racket authority unchanged

- **Original rationale:** Unknown. The selected canonical rule already matched all five canonical train/test pairs and passed rule smoke/authority parity.
- **Decision:** Do not edit the Racket program. Pin `RULE_HASH = "95bc32a62544"` and use Racket outputs as the production label authority.
- **Alternatives considered:** Rewrite the Racket rule; select the divergent archival program; make the Python mirror authoritative.
- **Why rejected:** No authority defect was reproduced. Changing the rule would expand scope and risk semantic drift. The Python mirror is retained only for tests and rival scoring.
- **Probe:** Final rule smoke, Racket lint, grammar, and authority-sync stages all pass.
- **Limit:** The archival source remains textually divergent; selected execution parity is what was verified.

## D2 — Replace advertised-but-dead controls with five exact axes

- **Original rationale:** Unknown. The baseline declared nine axes plus textures, but most were fixed, duplicated, inert, or bypassed in special modes.
- **Decision:** Expose only `grid_h`, `grid_w`, `n_pairs`, `palette_kind`, and `bend_pattern`. Validate every value and reject every unknown key.
- **Alternatives considered:** Keep compatibility aliases; mark dead axes diagnostic; declare large incompatibility tables.
- **Why rejected:** Compatibility aliases would preserve misleading API surface. All Cartesian combinations of the five real axes are feasible, so no incompatibility table is needed.
- **Probe:** `observe_overrides()` exactly recovers all five controls in every band; the 10,800-draw matrix has zero findings.
- **Failure modes:** A future axis addition must be observable from the grid or explicitly diagnostic; otherwise exact qualification should fail.

## D3 — Use canonical-sized profiles in every difficulty band

- **Original rationale:** Baseline dimensions were difficulty-linked but did not cover an exact canonical profile in easy.
- **Decision:** Draw from canonical dimension profiles: easy `(9,11)/(10,12)`, medium all five canonical sizes, hard `(10,13)/(11,13)/(12,10)`. Explicit overrides remain valid across the full `9..12 × 10..13` domain.
- **Alternatives considered:** Uniform dimensions independent of band; broad noncanonical sizes; one fixed canonical size.
- **Why rejected:** Uniform/fixed choices reduce curriculum breadth; broad sizes weaken linked profile support without adding rule branches.
- **Probe:** Final profile floor accepts 5/5 canonical inputs and records exact-profile support in 40/60 draws, with support in every band.
- **Limit:** The generator intentionally teaches the canonical size envelope, not arbitrary ARC dimensions.

## D4 — Schedule `2, 2, 3` endpoint pairs across each three-sample window

- **Original rationale:** Baseline generated only two pairs despite declaring broader color/pair axes.
- **Decision:** Default `n_pairs` cycles by `sample_index % 3` as `2, 2, 3`.
- **Alternatives considered:** Random independent pair count; always three; more demonstrations.
- **Why rejected:** Independent randomness can create complete three-demo lessons with only two-pair cases. Always-three drifts from all canonical examples. Three examples are sufficient when the third deterministically refutes the canonical-fitting “first two pairs only” shortcut.
- **Probe:** The shortcut fits all 5 canonical pairs but survives 0/300 generated lesson demo sets.
- **Failure modes:** A trainer that reorders or samples nonconsecutive generator indices would no longer inherit the window guarantee; the probe records the actual official sampler and start residues.

## D5 — Schedule palette and bend evidence across the same window

- **Original rationale:** Baseline palette textures were declared but ignored; bend direction was uncontrolled.
- **Decision:** Cycle `low`, `mid`, `high` palettes and `left`, `right`, `mixed` bend patterns over three consecutive samples.
- **Alternatives considered:** Uniform random colors/directions; keep named texture aliases; use only canonical colors.
- **Why rejected:** Deterministic window coverage makes lesson evidence auditable. Named aliases that do not change observable outputs are worse than no axis. The three palette groups preserve color diversity while remaining exact.
- **Probe:** All three schedule residues are represented in every band; witness counts are nonzero and both direction branches are heavily sampled.
- **Limit:** Palette names encode disjoint color bands, not a claim that color identity is semantically meaningful.

## D6 — Require disjoint authoritative paths

- **Original rationale:** The baseline placed endpoints but did not robustly guard the output rule against cross-color path collisions.
- **Decision:** Select endpoint pairs whose canonical vertical-then-horizontal paths are pairwise disjoint; make `self_check` reject intersections.
- **Alternatives considered:** Allow overwriting by color order; reject only endpoint overlap; repair collisions after drawing.
- **Why rejected:** Overwriting makes labels order-dependent and can hide part of a target path. Post-hoc repair complicates exact overrides and determinism.
- **Probe:** Dedicated mutation/regression test plus 600/600 strict semantic draws and 1,200/1,200 task-local probe inputs.
- **Failure modes:** The strict domain excludes potentially solvable but ambiguous collision cases by design.

## D7 — Declare concrete semantic rivals, not only morphology witnesses

- **Original rationale:** No semantic contract existed.
- **Decision:** Declare `horizontal_first` and `first_two_pairs_only` as lesson competitors; bind left/right/mixed witnesses to the former and three-pair witness to the latter; implement `lesson_identifiable` against real demo outputs.
- **Alternatives considered:** Witness frequencies only; generic dihedral shortcuts only; prose documentation.
- **Why rejected:** A witness can fire without refuting a wrong rule. Executable rivals allow the gate and future agents to measure actual disagreement.
- **Probe:** Battery verifies 4/4 rival claims; the 300-lesson probe reads declarations dynamically and reports zero survivor lessons.
- **Limit:** The rival set is deliberately finite. It covers the strongest observed alternatives, not every conceivable program.

## D8 — Cache geometry and traverse lazily

- **Original rationale:** Unknown. The first repaired draft regenerated and shuffled complete candidate pools for every draw.
- **Decision:** Cache pure candidate geometry by `(height, width, direction, band)`, encode occupied paths as integer bitmasks, and enumerate each pool via a deterministic coprime step without copying/shuffling it.
- **Alternatives considered:** Precompute all compatible triples; retain full `shuffle`; sample with replacement and retry.
- **Why rejected:** Full compatible-triple precomputation is memory-heavy; full shuffles made the qualification stage take minutes; replacement retries complicate deterministic exhaustiveness.
- **Probe:** A test uses an RNG whose `shuffle` raises, verifies cache hits, and still selects three disjoint paths. The final 10,800-draw override stage completed in 10.09 seconds.
- **Failure modes:** The cached domains grow with future dimension ranges; widening beyond current bounds should be profiled before adoption.

## D9 — Build a reusable source-bound lesson probe

- **Original rationale:** Required because the battery’s small lesson sample is only a smoke check.
- **Decision:** Add `workspace/lesson_probe.py`, which stages the selected runtime, uses the official sampler and canonical Racket oracle, reads declared rivals from the generator, and records source/probe hashes, unique inputs, residue coverage, domain failures, and disagreements.
- **Alternatives considered:** Copy rival names into an ad hoc notebook; score the Python mirror only; inspect generated grids manually.
- **Why rejected:** Copied rival lists drift, Python-only labels are not authoritative, and manual samples are not replayable.
- **Probe:** 300 lessons, 100 per band, passed with 1,200 unique inputs.
- **Limit:** The report explicitly limits its claim to the pinned finite census.

## Current parametric proposal — shorter-first path avoidance

The production generator v2.0.0 and exact canonical rule are unchanged. The native
`workspace/parametric/` adapter exposes `canonical` and `avoid_shorter`. The latter
routes in increasing Manhattan distance (reading-order ties), testing each elbow
against previously completed paths. This preserves endpoint-to-elbow reasoning
while making the later bend consume an input-dependent occupied-grid intermediate.
The wrong-intermediate witness holds ordering fixed and substitutes empty occupancy.

The separate grammar extends to 30x30 and nine pairs and permits collisions under
the canonical rule; the avoidance setting always has a clear candidate on sampled
scenes. If both candidates are blocked off this grammar, the Racket/Python total
fallback is vertical-first. Its tie/fallback fixture is explicitly off-distribution.

Two constructive lessons refute original-endpoint-only occupancy, no occupancy,
all-horizontal, longest-only, color priority, and height/width/area priorities.
The first two layouts remain structured teaching templates; palette, reflection,
geometry choices, later scenes and larger pair counts vary. No observed finite
teaching defect required repair in this build. The bounded 17-policy audit found
no harmful survivors; two greedy-order variants remain equivalent to canonical
outputs over this grammar and are honestly retained as survivors.

36 staged tests and the 32-seed audit pass; 55 protected-Racket audit executions
include actual labels, demo refutations and edge fixtures. Demos 2..6 (default 3),
four private prefix-stable queries, and one-query public projections are supported.
Owner acceptance remains pending; no training admission or universal uniqueness.
