# Working notes: ba090ac77d54

## 2026-09-28 review

The version-3.0 generator already had strong semantic coverage: every cyclic four-example window contained 3/4-seed cases and Manhattan-versus-Euclidean disagreements at both seed counts. The full before battery was green.

The remaining distribution shortcut was in the *metric-equivalent* controls. All four were produced by `_collinear_metric_same_layout`, so a learner could associate “seeds lie on one row/column” with metric equivalence. Version 3.1 retains the first pair as simple collinear controls and makes slots 4 and 5 non-collinear while requiring exact Manhattan/Euclidean label agreement. A bounded random search supplies ordinary diversity; an axis-aligned-corner construction is the deterministic fallback.

A regression test samples 120 draws (3 bands × 20 seeds × 2 slots) and requires valid inputs, zero metric disagreement, more than one seed row, and more than one seed column. The test failed against version 3.0 and passed after the implementation. The complete after battery remained 12/12 green.

The strongest canonical-fitting rival remains seed-count-conditioned distance: Manhattan for 3 seeds and squared Euclidean for 4. The canonical training set has only one 4-seed demonstration, and its two metrics agree. The scheduled 4-seed discriminator slots refute this rival. A replayable exact witness is stored in `workspace/shortcut_witness.json`.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `8da308ca4f853a97266e21fbfd4e3e32e8c7b93104371b1fc7a3393b5de237ee`.

# Decisions for `ba090ac77d54`

## D1 — Preserve the canonical rule

**Choice.** Do not edit the Racket authority or canonical row.

**Original rationale.** The rule already implements the intended framed Manhattan Voronoi fill, preserves nonzero cells, and writes cyan 8 exactly on minimum-distance ties.

**Alternatives considered.** Rewrite the rule for style, or change the canonical examples.

**Probe.** Before and after rule smoke, Python-mirror parity, and authority synchronization all passed. The canonical five pairs also match the mirror exactly.

**Failure mode avoided.** A gratuitous authority edit could create a source-selection mismatch without improving the input distribution.

## D2 — Preserve the eight-slot four-demo curriculum

**Choice.** Keep the schedule profiles and role ordering unchanged.

**Original rationale.** Every cyclic window of four samples contains:

1. a 3-seed metric-equivalent control;
2. a 4-seed metric-equivalent control;
3. a 3-seed Manhattan-versus-Euclidean discriminator; and
4. a 4-seed Manhattan-versus-Euclidean discriminator.

This directly refutes global and seed-count-conditioned Euclidean rivals while retaining all five public `(height, width, seed-count)` profiles.

**Alternatives considered.** Increase the schedule length, make all slots random, or replace controls with only disagreement cases.

**Probe.** All cyclic four-demo windows pass `lesson_identifiable` in easy, medium, and hard bands. The semantic gate reports all witnesses and named rival claims satisfied.

**Failure modes avoided.** A longer schedule could produce four-demo windows missing a decisive case. Removing equivalent controls would overteach “metrics always disagree” and reduce canonical resemblance.

## D3 — Break the collinearity proxy only in the second control pair

**Choice.** Keep slots 0/1 collinear and require slots 4/5 to be non-collinear with exact metric agreement.

**Original rationale.** Version 3.0 used `_collinear_metric_same_layout` for all four control slots. Collinearity therefore revealed the control class. Retaining one simple pair preserves an easy geometric teaching case; diversifying the second pair removes the perfect proxy.

**Alternatives considered.** Make every control non-collinear; use only fixed corner templates; or ignore the correlation because the decisive slots were already sound.

**Probe.** A test sampled 120 changed-slot draws. Before the implementation it failed immediately because slot 4 used a single row. After the implementation all draws were valid, non-collinear, and had zero label disagreement. The complete battery stayed green.

**Failure modes and mitigations.**

- Random search could fail: a verified corner-layout fallback is provided.
- A fixed fallback could collapse diversity: random search is attempted first, and seed/color/layout randomness remains.
- Non-collinearity alone does not guarantee metric equivalence: every candidate is checked by `_layout_is_teachable(..., metric_class="metric_same")`.

## D4 — Retain exact axis contracts

**Choice.** Leave `grid_h`, `grid_w`, and `n_seeds` as the only caller-facing exact overrides.

**Original rationale.** They are directly observable from the returned grid and already round-trip through the override contract.

**Alternatives considered.** Expose the semantic curriculum class as an override.

**Probe.** The override stage accepted 3420/3420 draws with no findings.

**Failure mode avoided.** Exposing `metric_class` would create a non-observable contract and complicate caller expectations.

## D5 — Preserve reproducible evidence rather than add shared tooling

**Choice.** Store the exact shortcut witness as task-local JSON in `workspace/shortcut_witness.json`.

**Rationale.** The packet forbids edits outside the selected task, and the existing semantic/battery tools already execute the needed checks. A source-bound, complete witness is more useful to a future reviewer than another overlapping shared runner.

**Probe.** The JSON records canonical fit, the generated input, intended and rival outputs, 12 differing coordinates, and direct Racket parity.

## Stopping decision

Stop after one focused distribution correction because the before implementation was already fully green, the identified proxy is now removed, all after gates remain green, and further changes would add risk without a demonstrated defect.
