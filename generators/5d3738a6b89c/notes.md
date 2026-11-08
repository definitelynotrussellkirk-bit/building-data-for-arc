# Working notes: 5d3738a6b89c

## Review repair

Baseline version 3.0.0 had stale fixed-11×11 metadata while `generate()` varied
height and box count, advertised dead/singleton axes, silently accepted unknown
or ignored overrides, supplied no observable override contract, produced zero
canonical-profile draws in the 60-draw floor, and declared no semantic witness or
rival. It also placed one or two anchors by capped rejection, allowing lessons
that did not necessarily distinguish “stamp every matching key” from “stamp only
the first key.”

Version 4.0.0 replaces that sampler with constructive geometry. Its only exact
axes are `grid_h`, `n_boxes`, `mask_size`, and `edge_mode`; every legal value is
honored in every difficulty band and recovered from pixels by
`observe_overrides()`. A 3×3 tile lattice gives exactly two anchors per key and
pairwise-disjoint stamp footprints. Mixed-edge inputs include a genuinely clipped
stamp. A weighted canonical-profile component retains 11×11, three-prototype,
five-color support without replaying canonical grids.

The canonical Racket authority was not modified. `reference_probe.py` provides an
independent Python oracle and the retained first-anchor rival. Focused regressions
were written before the repair; the baseline run was 24 failed / 12 passed, and
the final run is 36 passed. Final generator SHA-256:
`1a158e34a4d21a48d5736bdfcb3b0b0c10c91245a619d4f2a9703a3709a472b3`.

## Known domain limit

Generated boards intentionally use exactly two anchors per key. That guarantees a
teaching witness on every input, but it does not teach arbitrary anchor
multiplicity. Expanding to three or more anchors would require larger geometry or
an additional size/count axis and a fresh lesson-level shortcut census.
## Current reviewer considerations

Source SHA-256: `1a158e34a4d21a48d5736bdfcb3b0b0c10c91245a619d4f2a9703a3709a472b3`.

# Decisions — 5d3738a6b89c

## D0. Evidence source and authority

**Input choice.** I treated the immutable packet baseline, the three canonical input/output pairs, and the selected canonical Racket rule as authoritative. No prior return was used as a lead; `evidence/associated_notes.jsonl` was empty.

**Alternatives considered.** Reconstruct the intended distribution from the stale prose, or modify the Racket rule to fit the old sampler.

**Decision.** Preserve the rule and repair only the sampler, validator, tests, notes, and task-local tools. The rule already solved every canonical pair and was size-generic.

**Probe.** Rule smoke, grammar, authority sync, 64-case independent-oracle/Racket cross-check.

**Failure mode / limit.** The archival raw-code copy remains textually divergent from the selected callable, as authority sync reports, but execution parity passes. No canonical or Racket bytes were changed.

## D1. Advertise only four exact axes

| Axis | Final domain | Why it is meaningful | Pixel observation |
|---|---:|---|---|
| `grid_h` | 11–15 | Varies lower workspace height while preserving the top dictionary. | `len(grid)` |
| `n_boxes` | 2–4 | Varies dictionary size and derived width `4*n_boxes-1`. | Number of width-3 boxes |
| `mask_size` | 2–6 | Varies prototype complexity while retaining the center. | Uniform prototype nonzero count |
| `edge_mode` | `interior`, `mixed` | Distinguishes ordinary stamping from a genuinely clipped lower-boundary stamp. | Whether any anchor lies on a lower-region/grid boundary |

**Original rationale.** Unknown. Version 3 advertised nine axes, including aliases, constants, and controls not used by current generation.

**Rejected alternatives.** Keep `grid_w` as an independent axis; keep palette aliases; keep degenerate `texture` modes. Width is determined by box count, palette labels did not change a semantic branch, and degenerate identity/unmatched boards weakened training while violating the normal manifold.

**Probe.** The override contract exercises every legal value and multi-axis combination in every band. Final: 8,910 accepted draws, 99 cases, 0 findings. Focused tests also force `{grid_h:11,n_boxes:4,mask_size:6,edge_mode:mixed}` in all four difficulty settings.

**Failure mode / limit.** Derived width is not caller-controllable independently. That is intentional and documented rather than presented as an exact axis.

## D2. Strict override validation

**Decision.** Reject unknown keys, booleans masquerading as integers, wrong types, and out-of-domain values before constructing `GenCtx`. Consume every legal override through a keyed draw so provenance and returned pixels agree.

**Alternatives considered.** Continue reading `overrides.get()` directly; let `int()` coerce strings/bools; silently ignore unknown controls.

**Reason.** The baseline override audit produced 29,787 findings and accepted the unknown-key probe. Silent control failure is more damaging than a clear exception because downstream data jobs can believe a branch was sampled when it was not.

**Probe.** `test_invalid_or_unknown_overrides_are_rejected`; shared override gate.

**Failure mode / limit.** `difficulty` remains a sampling preference, not an exact override axis. Every advertised axis retains its full domain in every difficulty band.

## D3. Canonical-profile mixture

**Decision.** Add a keyed `curriculum_profile` draw. Canonical-profile draws weight height 11, three boxes, mask size 3, and interior placement while keeping every domain value available; broad draws use difficulty-specific preferences.

**Alternatives considered.** Replay canonical inputs, hard-code every fourth sample to 11×11, or opt out of the profile floor.

**Reason.** Replay risks leakage and low diversity; post-draw coercion would make provenance dishonest. Weighted keyed choices preserve natural variation and exact overrides.

**Probe.** Before 0/60 exact/envelope hits; after 27/60. Independent audit still found all 15 height/width combinations and every axis value in each band.

**Failure mode / limit.** Profile weighting correlates several axes. It does not reproduce canonical layouts or color choices, and exact controls can break the correlation.

## D4. Prototype colors and masks

**Decision.** Sample distinct keys from colors 1–8, excluding background 0 and separator 9. All prototypes in one generated grid share one exact `mask_size`; every mask includes the center; masks are distinct within the dictionary.

**Alternatives considered.** Retain the fixed color set `{2,4,6,7,8}`, allow different mask sizes per box, or permit centerless masks.

**Reason.** Broader colors reduce palette shortcuts. Uniform size makes `mask_size` exactly observable. The center must be nonzero because the canonical rule uses it as the lookup key.

**Probe.** Focused canonical/oracle tests, per-band distribution test, and independent audit.

**Failure mode / limit.** Uniform within-instance mask size is a sampler convention rather than a rule requirement; canonical pairs with unequal mask sizes remain accepted by `self_check` and `strict_canonical_like`.

## D5. Constructive anchor lattice

**Decision.** Partition the lower area into disjoint 3×3 tiles and place one anchor in each selected tile. Emit exactly two anchors per key.

**Alternatives considered.** Keep 40-attempt random placement, allow overlapping stamps, or emit one-or-two anchors randomly.

**Reason.** Constructive slots eliminate capped rejection, guarantee realized counts, and make every possible 3×3 footprint pairwise disjoint. Two anchors per key ensures every generated input refutes the canonical-fitting “first anchor only” shortcut.

**Probe.** 256-grid focused test, 1,500-grid independent audit, semantic gate, and 300-lesson census.

**Failure mode / limit.** Exactly two anchors is itself a constant distribution feature. Three-or-more anchors were rejected for this patch because the smallest legal geometry cannot fit them for every four-box combination without introducing incompatibilities or overlap.

## D6. Real edge clipping branch

**Decision.** In `mixed` mode, one anchor is placed on row 4 and its prototype is guaranteed to include a `dr=-1` mask cell. That offset is clipped by the rule’s lower-section boundary; all other anchors remain interior.

**Alternatives considered.** Call any near-edge placement “mixed,” or place an edge anchor whose mask happens not to cross the boundary.

**Reason.** A branch label must correspond to an executed semantic distinction, not merely a coordinate category.

**Probe.** Exact override observation and independent oracle/Racket cross-check include both modes.

**Failure mode / limit.** Only the top boundary of the lower region is forced. Left/right/bottom clipping is not separately controlled.

## D7. Validator contract

**Decision.** Validate: nonempty rectangular integer ARC grids; height 11–15; width `4*n-1`; unique full-9 separator at row 3; exact top divider columns; 2–4 pure width-3 prototypes; distinct valid center keys; mask sizes 2–6; only key colors below; equal anchor counts of one or two; and pairwise-disjoint realized footprints.

**Original behavior.** The validator mostly checked separator existence, box width, center colors, and presence of at least one lower key. It could accept mixed prototype colors, unequal counts, and destructive overlaps.

**Alternatives considered.** Validate generated grids only through metadata, or require exactly two anchors and uniform mask size universally.

**Reason.** Canonical support requires accepting one anchor per key and unequal prototype mask sizes. Pixel-derived validation is independent of generation bookkeeping.

**Probe.** Five destructive mutation families plus malformed-grid tests; shared mutation sensitivity 60/60.

**Failure mode / limit.** The validator intentionally describes the reviewed sampler plus canonical pairs, not every mathematically lawful size-generic input the Racket program could execute.

## D8. Semantic witness and rival

**Decision.** Declare `repeated_key_anchors` and one shared function `first_anchor_per_key_only` through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.

**Why this rival.** It matches all three canonical pairs because each canonical key occurs once below the separator, yet it is wrong for the stated “every matching key” rule.

**Alternatives considered.** A no-clipping rival or a fixed-11×11 rival. Those would require lesson scheduling guarantees because many lawful individual draws do not refute them. The selected rival is refuted by every generated input.

**Probe.** Canonical fit 3/3; semantic gate 60/60 rival checks; independent audit 1,500/1,500 disagreements; lesson census 300/300 refutations for each declaration.

**Failure mode / limit.** A finite declared rival set is not a proof of universal identifiability. The source-bound census also does not rotate every pair into every possible query position.

## D9. Independent task-local tooling

**Decision.** Add `workspace/reference_probe.py` rather than reuse parser/stamping functions from the generator.

**Capabilities.** Portable canonical loading, independent parsing, independent oracle, first-anchor rival, pixel observation, footprint analysis, deterministic replay, branch coverage, and JSON audit output.

**Reason.** Tests that share production helpers can reproduce the same bug and falsely agree. The tool is reusable by future reviewers and can point at an alternate generator path.

**Probe.** CLI count 500 per band, exit 0; probe SHA-256 retained in its report.

**Failure mode / limit.** The probe is still a Python transcription. The 64-case canonical Racket cross-check is retained to test transcription parity.

## D10. Test-first repair

**Decision.** Write focused tests before replacing the sampler. The first source-bound run was retained at 24 failed / 12 passed; the same suite passed 36/36 after implementation.

**Coverage.** Canonical acceptance/oracle parity, rule hash, exact controls in all bands, invalid controls, domain coverage, canonical-profile presence, determinism, two anchors, nonoverlap, semantic rival behavior, destructive mutations, malformed inputs, and Python hash-seed independence.

**Alternative rejected.** Modify production code first and write tests around its observed behavior. That would risk encoding the baseline defect as the expectation.

## D11. Racket authority unchanged

**Decision.** No Racket/canonical data edit.

**Reason.** The rule is correct on canonical pairs, size-generic, reentrant, and matched the independent oracle on 64/64 varied final inputs. All measured defects were in sampling, contracts, and validation.

**Probe.** `rule_smoke`, `grammar`, `racket_lint`, `authority_sync`, and `arcpuzzles apply` cross-check.

**Failure mode / limit.** The selected authority remains catalog-unapproved/train-safety-unverified in this packet; this return does not change admission state.

## 2026-10-24 follow-up repair — outer clipping closure

This section supersedes the “only top boundary is forced” limit in D6 and extends D8–D10.

### D12. Mixed mode exercises two distinct clipping surfaces

The retained audit found that version 4.0.0's `mixed` branch always placed one anchor immediately below the separator but never placed an anchor on the outer left, right, or bottom grid border. A solver that ignored outer-border anchors therefore fit all canonical examples and 600 audited generated draws.

Version 4.1.0 reserves two distinct 3×3 lattice tiles in every mixed scene:

1. the first prototype has a `dr=-1` offset and an anchor on row 4, exercising clipping against the lower-section boundary at row 3;
2. the second prototype has a `dc=-1` offset and an anchor on column 0, exercising clipping against the outer left grid edge.

The remaining anchors still use distinct tile centers. Realized in-bounds stamp footprints remain pairwise disjoint, so the original constructive overlap proof is preserved.

Rejected alternatives: random near-edge sampling, relabeling any boundary anchor as mixed, or adding a fifth public edge-surface axis. The defect was missing semantic execution, not insufficient metadata. One deterministic mixed contract is easier to audit and teaches both clipping classes.

### D13. Two-demo edge schedule and outer-border rival

`EXAMPLES_NEEDED = 2`, `SCHEDULE_EDGE_MODES = (interior, mixed)`, and `schedule_edge_mode()` make every sliding two-demo default window contain both branches. Explicit `edge_mode` overrides still take precedence and remain exact in every difficulty band.

The new canonical-fitting rival `outer_border_anchor_ignored` skips lower anchors located on the outer left/right/bottom border. It matches all three canonical pairs because none contains such an anchor. Every default mixed scene with mask size at least three paints at least one additional in-bounds cell from the outer anchor, so the rival disagrees with the authoritative stamp.

The semantic declarations now contain two aligned witness/rival pairs:

- `repeated_key_anchors` → `first_anchor_per_key_only`;
- `outer_grid_clipping` → `outer_border_anchor_ignored`.

Both rivals are shared across `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`. `rule_mirror`, `semantic_observables`, and `lesson_identifiable` were added to make the lesson contract executable rather than metadata-only.

### D14. Exact mask-size-two ruling

A 2-cell prototype can consist only of the center plus one outward offset. At an outer-border anchor that non-center cell is clipped, so stamping the anchor adds no in-bounds pixel beyond the already-present center. Skipping that one anchor is therefore observationally identical, even though real clipping occurred.

Decision: preserve exact `mask_size=2, edge_mode=mixed` as a lawful clipping example, but schedule default mixed lessons with mask size 3–6 and require the outer prototype to contain both an outward offset and an in-bounds non-center offset. Interior defaults continue to sample size two, so the advertised domain remains covered.

Cost/limit: a size-two mixed example alone does not refute the outer-anchor-skipping rival. Every default two-demo lesson does. This distinction is encoded in focused tests and documented rather than hidden by changing the public domain.

### D15. Independent probe extension and evidence

`workspace/reference_probe.py` now reports actual clipping surfaces (`separator`, `left`, `right`, `bottom`) from each anchor/mask pair and independently implements the outer-border rival. Its version-2 audit checks canonical fit, deterministic replay, overlap, exact branch counts, and rival disagreement.

Evidence retained under `WORK/checks/5d3738a6b89c-*`:

- Source-bound RED: all prior 36 tests passed; 12 new clipping/schedule/rival tests failed against version 4.0.0.
- GREEN: 48/48 focused tests passed.
- Independent audit: 180 samples in each of easy/medium/hard (540 total), zero validation errors, zero nondeterminism, zero overlaps, 540 distinct inputs, 270 separator-clipping scenes, 270 outer-clipping scenes, and 270 outer-border-rival disagreements. Both canonical shortcuts match all three canonical labels.

The canonical Racket authority remains unchanged.


### D16. Query-rotation closure

D13's period-2 `interior, mixed` schedule was sufficient only when the query stayed after the two ordered demonstrations. Exhaustive period enumeration exposed three ambiguous rotations: in an `interior, mixed, interior` episode, holding out the sole mixed pair left two interior demonstrations, allowing `outer_border_anchor_ignored` to survive. A focused regression reproduced this before the change.

Version 4.2.0 uses period three with `SCHEDULE_EDGE_MODES = (mixed, mixed, interior)`. Every consecutive two-demo window still contains a mixed scene, the interior branch remains scheduled, and every three-pair episode has two mixed scenes so any one holdout leaves an outer-clipping witness. The focused suite is 49/49 green; the source-bound fixed-seed receipt passes every rotation; the independent probe reports 36/36 clean rotations and 360/540 mixed scenes; and 27/27 fresh inputs match the unchanged Racket authority. This supersedes only D13's period-2 scheduling statement; D12–D15's clipping construction and size-two ruling remain unchanged.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e0ef5912d9f208fb:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `1a158e34a4d21a48d5736bdfcb3b0b0c10c91245a619d4f2a9703a3709a472b3`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source6e19b085bbf7ad281a2ccb6f1b4e1fb0fdee908ab379e52e2bdfab778d4e014d constructively includes outer-grid and separator clipping, with mixed/mixed/interior scheduled witnesses retained under supported two-demo holdouts.49tests and27Racket comparisons plus bounded period checks are reviewer-reported. Exact mask_size2/mixed remains a documented diagnostic limit.

### Assessment or prior finding

## 5d3738a6b89c

**Finding A1 — outer-grid clipping is lawful but not sampled.** The task's pinned source SHA-256 is `1a158e34a4d21a48d5736bdfcb3b0b0c10c91245a619d4f2a9703a3709a472b3`; rule hash `f9d79bf79624`. Canonical anchors and 600 ordinary generated draws (200 per band) never place an anchor on the outer left/right/bottom border. The `mixed` branch exercises clipping only immediately below the separator. Therefore the plausible shortcut “stamp normally except leave outer-border anchors unexpanded” fits all 3 canonical pairs and all 600 sampled draws.

A lawful 11×7 witness places a color-2 anchor at the left border under a horizontal three-cell prototype. `self_check` and `strict_canonical_like` both return `[]`. The intended rule clips the left prototype cell and paints the in-bounds right cell; the shortcut leaves only the original border anchor. The supported Racket application, executed rule hash `f9d79bf79624`, matches the independent intended output and differs from the shortcut.

Evidence:

- exact input: `checks/audit/5d3738a6b89c/input.json`
- Racket output and hashes: `checks/audit/5d3738a6b89c/racket.json`
- rival output: `checks/audit/5d3738a6b89c/rival.json`
- source-bound probe and counts: `checks/audit/5d3738a6b89c/probe.json`
- reusable audit probe: `checks/audit/5d3738a6b89c/outer_edge_probe.py`
- existing task tests: `checks/audit/5d3738a6b89c-task-tests/` — 36 passed

**Suggested repair direction, not applied:** add a schedule profile with a prototype whose nonzero mask crosses an outer border and an anchor on that border, while preserving nonoverlapping footprints. Keep separator clipping and outer-grid clipping as separate witnesses.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e0ef5912d9f208fb-v0001/audit_assets.json), manifest SHA-256 `427015e1125a84207cd21fc59f98ebc7b812a525ee64bacdcff5f9572bdfa788`.
<!-- arcpuzzles-current-audit-assessment:end -->
