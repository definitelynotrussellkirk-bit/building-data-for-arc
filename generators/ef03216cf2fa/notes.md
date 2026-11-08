# Working notes: ef03216cf2fa

## Native parametric family — reviewer ready, owner acceptance pending

- `workspace/parametric/adapter.py` preserves the exact canonical perimeter-ranking program and adds `ranking=normalized_top_edge`: count occupied top-edge cells after clockwise normalization, rank descending with source-position ties, and retain the canonical stacking operation.
- Dependency: normalized crops -> their input-dependent edge counts -> object order. Protected witnesses keep displayed crops fixed and substitute original-top measurements; both a three-object and a six-object 30x30 query change order. Returned evidence: `checks/ef03216cf2fa/causal/witness.json` and sibling replay.
- Supports 2–6 demonstrations and 1–4 independent queries; ordinary qualification uses three demos/four queries. Input streams are identical across settings. Two demos jointly refute 16 declared shortcuts under both settings; a bounded 48-candidate cover fails explicitly if unavailable.
- Separate query grammar expands to 3–6 distinct-color objects on 10x12, 16x20, 24x25 and 30x30 canvases. Connected shapes include split-edge combs, bridges, crosses, frames and corner-Ls; large scenes contain six substantive objects and border contacts. Canonical production remains unchanged.
- Fresh checks: 27 focused tests; 8/8 Racket-backed lessons at 2,3,6 demos, 60 labels, 32 query targets, 480 protected executions. Native qualification passed both settings on seeds 0 and 17; exact source inventory is `workspace/parametric/evidence/manifest.json`. Returned native receipts are `checks/ef03216cf2fa/qualification/{qualification,execution}.json`.
- `workspace/parametric/check.py` replays chosen labels and demonstration-only rivals and writes hash-named single-query public projections. Private settings, programs, future queries and all query answers remain controller-side. This is a static export/check helper, not a turn controller.
- Limits: finite rivals/seeds only, separated bounding boxes and distinct object colors, no measured learning gain. Wrong-rotation/no-rotation rivals are replayed on demonstration inputs, not large queries. Source is native-qualified reviewer evidence; the owner must freshly qualify and accept the exact integrated bytes. No training admission.

## Current contract

- Intended rule: find same-color 4-connected nonzero objects; crop each bounding box; rotate a tall crop 90 degrees clockwise; sort by bounding-box perimeter descending with original row-major position as the tie-break; stack crops vertically, left-aligned, with one zero row between them.
- Selected Racket authority is unchanged and pinned by `RULE_HASH = "455db4f731f0"`.
- Version `3.0.0` emits 3 or 4 separated objects on 10–14 by 10–14 grids. Generated perimeters are distinct, 1 or 2 objects are tall, and every tall crop is asymmetric under clockwise versus counterclockwise rotation.
- Exact controls are `grid_h`, `grid_w`, `n`, `tall_count`, `rank_layout`, and `palette_family`; every cross-product is constructive in every difficulty band. Unknown, mistyped, and out-of-range overrides are rejected.

## Review findings and reversals

1. **Canonical shortcut.** All four canonical pairs are also fit by rotating tall crops counterclockwise, because their tall crops are rotation-direction symmetric. The old generator did not guarantee a distinguishing input. The replacement makes every generated tall crop an asymmetric corner-L family member and declares the counterclockwise rival through the semantic contract. Exact retained witness: `counterexamples/review-d5c9325712268b53-counterclockwise/`.
2. **Unobservable controls.** Version `2.0.0` advertised broad generic axes that were dead, overlapping, or incompatible with actual draws. The new six-axis surface contains only properties that can be recovered from the grid by `observe_overrides`.
3. **Difficulty behavior.** An intermediate replacement produced byte-identical easy/medium/hard samples. The final bands change only hidden placement offsets, preserving the same legal override domain and semantic difficulty. This is deliberately modest; no band narrows the exact controls.
4. **Canonical-profile floor.** An intermediate random size schedule missed the pinned easy-band profile floor. Defaults now draw from `(10,10,3)`, `(10,12,3)`, `(11,11,4)`, and `(12,12,4)`, while explicit overrides retain the complete 10–14 and 3–4 domains.
5. **Tie policy.** Generated perimeters are distinct so perimeter sorting is teachable. Canonical tied-perimeter inputs remain valid and use the Racket rule's row-major tie-break; the validator does not incorrectly reject them.

## Verification and limits

- Final generator SHA-256: `b4a25d2fcfdf038eb6ce56eae11105ae452d7680d7358cd182bd9f6411b4332c`.
- Aggregate battery: 12/12 green (`checks/after-final/checks/ef03216cf2fa_after_battery_summary.json`).
- Focused suite: 193 passed, including a red-on-baseline/green-on-repair retained counterexample regression.
- Required-rotation semantic gate: 600/600 strict hits and 600/600 clockwise-direction witnesses across 200 draws per band.
- Lesson census: 300 lessons, 1,200 labeled pairs, 1,200 unique inputs, and all 1,200 query rotations had no ambiguity against the declared counterclockwise rival.
- This evidence tests a finite declared-rival family, not every conceivable ARC hypothesis. Generated shapes are intentionally limited to small connected corner-L variants, generated perimeters are distinct, and generated scenes contain only 3–4 objects. Canonical support is broader where explicitly checked (notably perimeter ties).
- No earlier return for this task was used as a repair lead; the immutable baseline, canonical examples, battery failures, and independently written oracle drove the changes.
## Current reviewer considerations

Source SHA-256: `b4a25d2fcfdf038eb6ce56eae11105ae452d7680d7358cd182bd9f6411b4332c`.

# Decisions: ef03216cf2fa

## D1 — Preserve the selected rule; repair the generator

**Choice.** Keep the canonical Racket authority unchanged and pin its catalog hash (`455db4f731f0`) in Python.

**Rationale.** The Racket program reproduces all canonical outputs and the independent Python oracle agrees on generated witnesses. The defect was that the old sampler neither represented its controls faithfully nor distinguished rotation direction.

**Alternatives rejected.** Rewriting the rule, changing canonical labels, or weakening the task to omit rotation would alter a correct authority to accommodate a deficient distribution.

**Probe / failure mode.** Rule smoke, authority sync, the independent oracle, and the retained Racket witness all agree. Remaining limit: agreement on tested inputs is not a proof of equivalence for arbitrary malformed grids.

## D2 — Use six exact, observable controls

**Choice.** Expose only `grid_h`, `grid_w`, `n`, `tall_count`, `rank_layout`, and `palette_family`.

**Rationale.** Each value is recoverable from the emitted grid and affects construction. The full categorical cross-product is legal in every band, with no hidden incompatible combinations.

**Alternatives rejected.** The baseline's generic `anchor_corner`, `asymmetry_force`, `palette_size`, `position_bias`, `n_distinct_colors`, and texture aliases were dead, redundant, or not exact controls. Keeping them would preserve an API fiction.

**Probe / failure mode.** `observe_overrides` is checked against all 144 categorical/band combinations with both object-count/tall-count pairs, and invalid types/ranges are tested. The observer depends on generated perimeters being distinct; canonical ties are handled by the rule but are intentionally outside generated rank-layout observation.

## D3 — Default to canonical-size profiles while preserving a wider explicit domain

**Choice.** Default profiles are `(10,10,3)`, `(10,12,3)`, `(11,11,4)`, and `(12,12,4)`; explicit grid overrides remain 10–14 and `n` remains 3–4.

**Rationale.** This guarantees each pinned band can hit an exact canonical size/palette-count profile while retaining useful explicit coverage. An intermediate uniform schedule produced 4/60 exact hits overall but none in easy, so it failed the profile-floor gate.

**Alternatives rejected.** Narrowing the advertised domain to only four profiles would make override coverage unnecessarily small. Pure uniform defaults had a finite but unacceptable chance of missing a band-specific floor.

**Probe / failure mode.** The final profile-floor stage is green and a focused regression reproduces the pinned 20-draw seed recipe. The schedule does not claim to reproduce every canonical geometry.

## D4 — Make every tall crop direction-sensitive

**Choice.** Construct connected corner-L shapes spanning 2×3, 2×4, 3×4, or transposed tall boxes, with an optional adjacent detail that never fills the crop.

**Rationale.** Every canonical tall crop is clockwise/counterclockwise symmetric, so a sparse occurrence of an asymmetric witness would leave many lessons underdetermined. Requiring asymmetry in every generated tall object makes the intended direction continuously observable.

**Alternatives rejected.** A low-probability witness branch, only one fixed hand-authored witness, or relying on textual metadata would not guarantee teachable generated lessons.

**Probe / failure mode.** The semantic gate observed 600/600 witnesses; the 300-lesson census refuted the counterclockwise rival in every production and rotated-query lesson. The finite rival set does not cover unrelated transformations that happen to agree on this shape family.

## D5 — Distinct generated perimeters; preserve canonical tie behavior

**Choice.** Use bounding-box side sums 4, 5, 6, and 7 as needed, yielding pairwise distinct perimeters. Sort descending and use row-major source position on ties.

**Rationale.** Distinct generated ranks teach perimeter ordering rather than accidental spatial order. The canonical ledger includes a tied case, so the validator and oracle retain the authority's row-major tie-break.

**Alternatives rejected.** Rejecting all ties would falsely reject canonical input; generating frequent ties would make `rank_layout` unobservable and weaken the intended discriminator.

**Probe / failure mode.** Canonical-pair tests include the tied example. Generated cross-product tests assert distinct perimeters. Generated data therefore teaches the primary perimeter rule more strongly than the secondary tie policy.

## D6 — Control spatial rank layout independently of semantic order

**Choice.** Place perimeter ranks in ascending, descending, or interleaved row-major slot order.

**Rationale.** This breaks the shortcut “read objects in source order” while keeping the semantic sort target fixed. All layouts are visible and deterministic under exact override.

**Alternatives rejected.** Fully random, unlabelled layout would be harder to audit; a single fixed layout would allow a source-order shortcut.

**Probe / failure mode.** The independent observer recovers all three layouts. Only four corner slots are used, so arbitrary spatial arrangements remain outside this generator's domain.

## D7 — Use low, high, and mixed palettes without assigning semantic roles to color values

**Choice.** Sample distinct colors from `1..4`, `6..9`, or both.

**Rationale.** Perimeter and orientation—not numerical color—determine output order and rotation. Palette families prevent a fixed low/high color heuristic from serving as a stable semantic role.

**Alternatives rejected.** One fixed palette or rank-correlated colors would create avoidable shortcuts. Color 5 is omitted so low/high/mixed are unambiguous to observe.

**Probe / failure mode.** Cross-product tests recover each family exactly. This is not a claim that color 5 is illegal in the canonical task; it is a deliberate generated-domain boundary.

## D8 — Difficulty changes hidden placement only

**Choice.** Easy, medium, and hard shift the same four placement slots by small offsets; they do not narrow the override domain or change rule semantics.

**Rationale.** An intermediate implementation ignored difficulty completely and triggered the dead-band detector. Small deterministic shifts make the bands non-identical without conflating difficulty with fewer controls or missing witnesses.

**Alternatives rejected.** Reducing object count in easy or forbidding layouts/palettes by band would make advertised exact controls conditionally invalid. Artificially enlarging shapes in hard would add a second distribution change not required by the task.

**Probe / failure mode.** A focused regression verifies three byte-distinct grids under identical controls and identical recovered axes. The bands are distribution labels, not calibrated human-difficulty guarantees.

## D9 — Three demonstrations and one query; support arbitrary query position

**Choice.** Keep `EXAMPLES_NEEDED = 3`. The production sampler assembles 3 demonstrations + 1 query; the large census also holds out each pair in turn.

**Rationale.** Because every generated pair itself distinguishes clockwise from counterclockwise, three demonstrations are sufficient against the declared rival while retaining the existing lesson format.

**Alternatives rejected.** Increasing the count would add cost without addressing a surviving declared rival. Claiming query-position independence from production-order checks alone would be unsupported.

**Probe / failure mode.** `checks/lesson-census-final.json`: 300 production lessons and 1,200 query rotations, all unambiguous against the declared rival. This does not enumerate every possible schedule start or undeclared hypothesis.

## D10 — Add an independent oracle and a retained source-bound counterexample

**Choice.** Keep `workspace/reference_probe.py`, a task-local 193-test suite, and the exact Racket/Python witness directory.

**Rationale.** Testing the generator only with its own helpers could preserve a shared implementation error. The portable probe independently extracts components, rotates, sorts, packs, loads canonical pairs, and observes axes.

**Alternatives rejected.** A prose-only review or an unbound screenshot would not be replayable by future agents.

**Probe / failure mode.** The counterexample regression fails against the frozen `2.0.0` baseline and passes against `3.0.0`. The probe still shares Python's basic grid representation and is not a second Racket implementation.
