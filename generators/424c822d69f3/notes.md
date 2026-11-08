# Working notes: 424c822d69f3

## Current rule and domain

Row 0 is a legend of 2–4 distinct nonzero, non-5 marker colors. Row 1 is blank. Every lower nonzero component is a solid color-5 rectangle. For each rectangle, compute the integer midpoint of its horizontal bbox as `(left + right) // 2`; recolor the component with the uniquely nearest row-0 marker color.

The integer midpoint is authority behavior, not a cosmetic convention: the selected Racket runtime maps exact-integer division to quotient, so even-width boxes use the left middle column. Exact nearest-marker ties are rejected because the canonical examples do not teach a tie policy.

Canonical rule hash: `5abbdbb61293`. Current generator version: `2.2.0`.

## Reversed decisions

- **Ties:** the pinned sampler admitted exact ties; now construction and `self_check` exclude them. Lead: retained audit `review-450aec7fa7739013:v0001`.
- **Center arithmetic:** an intermediate geometric-center mirror was wrong for even widths; all current code and tests use the executable floored midpoint.
- **Textures:** unsupported/degenerate texture metadata was removed. The public surface is seven exact, observable axes.
- **Authority duplicate:** active base `target_code` is synchronized with canonical authority; archival `raw_code` remains unchanged.

## Teaching contract

Every ordinary default sample contains:

- `shared_nearest`: multiple rectangles use the same nearest marker, refuting left-to-right rank pairing;
- `nearest_outside_bbox`: at least one assigned marker lies outside the rectangle span, refuting vertical-overlap-only coloring.

`EXAMPLES_NEEDED = 3`. The period-six schedule has two canonical anchors plus edge, left-large, right-varied, and scattered profiles. Named competitors are checked by `lesson_identifiable` for every query rotation supported by the census.

## Evidence

- Portable focused tests: 80/80 (`checks/task-tests-final/`).
- Racket parity: 53/53 (`checks/racket-parity-final.json`).
- Random lesson census: 300/300 lessons, 1,200 rotations, zero declared-rival ambiguity (`checks/lesson-census-final.json`).
- Fixed-seed schedule enumeration: 18/18 starts, 72 rotations, zero ambiguity (`checks/schedule-census-final.json`).
- Final battery: 11/12 green; semantic gate exits 1 only because it requires declared schedule enumeration to be reported separately. The separate enumeration is complete.

## Known limits / open findings

- The generator deliberately does not teach authority behavior on exact ties.
- Rival coverage is finite (`rank_order`, `vertical_overlap_only`); it is not a universal proof of induction.
- Schedule enumeration exhausts starts at seed 0 only; the larger random census broadens but does not exhaust seed coverage.
- Explicit override samples are exact and lawful but need not carry every default teaching witness.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-450aec7fa7739013:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `4a6960ae8b40595dd7d32a95c65a4cbfa8e96b128133c74f415ad71f7775f83c`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Exact nearest-marker ties on baseline4a6960ae8b40 addressed by acceptede4d659 return6f2a8be446d2: constructive unique nearest under actual selected-runtime integer center semantics, strict validation,80 reported tests,53 real-Racket parity checks,300lesson/1200rotation census. Preserve original11/12 aggregate plus separately reported18lesson/72rotation schedule census; no independent rerun or full semantic-proof claim.

### Assessment or prior finding

## 424c822d69f3

**Reproduced teaching ambiguity: generated exact nearest-marker ties have no canonical tie policy.** Generator SHA-256 `4a6960ae8b40595dd7d32a95c65a4cbfa8e96b128133c74f415ad71f7775f83c`; executed rule hash `5abbdbb61293`.

The generator's own `(seed=0, sample_index=0, difficulty=None, overrides={})` output passes `self_check` and contains a color-5 rectangle with bbox rows 4–6, columns 2–4, hence center column 3.0. Row-0 markers at columns 2/color 4 and 4/color 6 are exactly equidistant. The selected Racket rule resolves the `argmin` tie by marker order and recolors the rectangle to 4. A plausible rival—same bbox-center nearest-marker rule, but exact ties choose the right marker—recolors it to 6 and differs on nine cells.

The rival fits all 3/3 canonical training pairs because none contains a different-color exact tie. This is not rare under the current sampler: with seed 0 and sample indices 0–99, different-color ties occurred in 22/100 default, 30/100 easy, 22/100 medium, and 11/100 hard samples; all 400 samples passed `self_check`. The task's own description metadata says to avoid exact center-column ties unless a policy is specified, so these examples should be rejected/resampled or the tie policy should be deliberately taught.

Evidence: `checks/audit/424c822d69f3/counterexample.json`, `input.json`, `racket.json`, `rival.json`, `canonical-rival-check.json`, and `sampling.json`. The supported Racket command and effective cwd are embedded in the receipt. Audit only; target source was not changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-450aec7fa7739013-v0001/audit_assets.json), manifest SHA-256 `71daf743f09463d817cb04f91fc510e0b3473ca6157f1324c520ab0dd60a9001`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `6f2a8be446d2bb9e96302063bcb891fbe1459f128607995ffbdef49487e3825a`.

# Decisions for 424c822d69f3

## D1. Exclude exact nearest-marker ties

**Prior choice.** The pinned sampler permitted an object midpoint to be equally distant from differently colored row-0 markers. The original rationale is unknown.

**New choice.** Exact ties are illegal in `self_check` and are skipped by constructive placement.

**Why.** All three canonical demonstrations avoid ties, so “choose the left marker” and “choose the right marker” both fit them. The retained baseline input at `repo/generators/424c822d69f3/counterexamples/review-450aec7fa7739013-v0001/` differs on nine cells under those two policies.

**Alternatives.** Deliberately teach stable-left tie-breaking; encode marker order as part of the prose; leave ties rare. These were rejected because they enlarge the learned rule beyond the canonical evidence.

**Probes.** Focused tests retain the old tie, require rejection, and sample 120 defaults per band without ties. Racket parity and lesson censuses use only uniquely defined cases.

**Limitation.** The selected Racket program still has behavior on ties; the generator intentionally defines a narrower teaching domain.

## D2. Follow executable integer midpoint semantics

**Prior choice.** Early repair code used a geometric center, making an even-width bbox midpoint half-integral.

**New choice.** Use `c0 + (width - 1) // 2`, equivalent to `(c0 + c1) // 2`.

**Why.** The selected Racket runtime implements exact-integer division as quotient. An apparently unique geometric case was therefore an executable tie and produced the left marker.

**Alternatives.** Change the Racket rule to exact rational centers; restrict all rectangles to odd widths. Changing authority was unjustified, while odd-only widths would unnecessarily shrink the domain.

**Probes.** Tests include the semantic-gate counterexample and a legal even-width case; the independent oracle and 53-case Racket parity report agree.

**Limitation.** Readers expecting Euclidean rectangle centers must be told that “center” means the executable integer midpoint.

## D3. Replace rejection-heavy random scenes with constructive exact scenes

**Prior choice.** The baseline mixed several controls and textures whose requested values were not always observable, and some combinations crashed or degenerated.

**New choice.** Draw a finite exact profile, place a deterministic marker signature, choose rectangle dimensions, then search only lawful separated placements with unique nearest markers. Unknown and out-of-range controls fail before generation.

**Why.** This guarantees lawful output, deterministic replay, and exact provenance without silently relaxing controls.

**Alternatives.** Generate freely and resample; keep approximate density/texture knobs; declare incompatible combinations. Constructive placement gives clearer failures and allowed the advertised Cartesian domain to remain supported.

**Probes.** The portable 80-test suite checks exact boundary overrides and pixel round-trips; the official override stage is green with no warning categories.

**Limitation.** Explicit overrides are lawful but may remove the stronger default teaching witnesses.

## D4. Retire texture as a public axis

**Prior choice.** Metadata advertised helpful/degenerate texture names, including a `single_marker` behavior that could pass an insufficient validator; some advertised names were unsupported by generation.

**New choice.** `HELPFUL_TEXTURES`, `DEGENERATE_TEXTURES`, and lawful-degenerate textures are empty. Geometry, layout, scale, and palette are represented directly by exact axes.

**Why.** A nominal texture label that cannot be recovered from pixels or does not execute is not a reliable control.

**Alternatives.** Repair every legacy texture; keep them as hidden diagnostics. They were not needed to teach the rule, so removal was smaller and safer.

**Probes.** Lint, defect lint, overrides, and focused unknown-control tests all pass.

**Limitation.** Callers using legacy texture names now receive an explicit error rather than a compatibility mapping.

## D5. Make default samples refute canonical-fitting shortcuts

**Prior choice.** Canonical-like scenes often let objects pair with markers by left-to-right rank or only when a marker sat directly above the object.

**New choice.** Every ordinary default sample must contain:

1. at least two objects assigned to the same nearest marker (`shared_nearest`),
2. at least one object whose assigned marker lies outside the object's horizontal bbox (`nearest_outside_bbox`), and
3. a rank-order mismatch.

The corresponding rivals are executable `rank_order` and `vertical_overlap_only` functions, exposed through the lesson contract.

**Why.** Both rivals fit all canonical demonstrations but are semantically plausible. Refuting them in each ordinary scene makes every three-demo lesson robust to ordering and query rotation.

**Alternatives.** Rely on aggregate frequency; place one witness per three-example lesson. Per-example witnesses simplify schedule reasoning and survive arbitrary query rotation.

**Probes.** Semantic gate: both witnesses 600/600 and claims 60/60. Random census: 300 lessons, 1,200 rotations, zero ambiguity. Schedule census: 18 starts, 72 rotations, zero ambiguity.

**Limitation.** These are declared-rival guarantees, not a proof against undeclared hypotheses.

## D6. Use a six-step schedule with explicit canonical anchors

**Prior choice.** Baseline profile support was too sparse and scale metadata did not reliably match canonical shape/palette.

**New choice.** Period-six profiles are `edge_overlap`, two `canonical_anchor` positions, `right_varied`, `left_large`, and `scattered_small`. Anchors are 10×10 with three markers, three 2×2 rectangles, and one canonical palette family. Large rectangles are 2×7 (area 14), matching canonical scale without breaking vertical packing.

**Why.** This gives every band measurable exact canonical-profile support while preserving broad sizes, layouts, palettes, and object widths.

**Alternatives.** Anchor every sample; one anchor per period; use taller large rectangles. Two anchors met the profile floor without collapsing diversity; 2×7 remained packable in all lawful heights.

**Probes.** Final profile floor: 27/60 exact hits, with easy 9/20, medium 6/20, hard 12/20. Diversity and grammar stages are green.

**Limitation.** Difficulty labels describe the non-anchor distribution; each band intentionally contains occasional 10×10 anchors.

## D7. Synchronize the selected active authority duplicate

**Prior choice.** The selected base solution's active `target_code` had different Racket text from canonical authority, although archival behavior was intended to be equivalent.

**New choice.** Copy canonical `program_solution` into active `racket_target.target_code`, set canonicalization metadata, and retain `raw_code` unchanged.

**Why.** Authority-sync should bind the selected executable target to the declared canonical source without erasing provenance.

**Alternatives.** Change canonical authority; delete archival code; ignore textual divergence. All were rejected.

**Probes.** Final authority-sync is green and reports `selected_synchronized_archival_divergent`; execution parity passes.

**Limitation.** Archival `raw_code` remains textually different by design.

## D8. Build a task-local independent oracle/probe

**Choice.** Add `workspace/reference_probe.py`, independent of production generator internals, for component extraction, floored-midpoint output, exact-control observation, rivals, witness facts, and Racket batch execution.

**Why.** The most important defect arose from Python/Racket semantic drift. A separate oracle makes future changes auditable and gives agents a reusable source-bound probe.

**Alternatives.** Reuse private generator functions in tests; trust only the Python mirror. Those approaches would share the same bug surface.

**Probes.** The 53-case parity report has zero mismatches and binds generator SHA-256 and rule hash.

**Limitation.** The probe is task-specific and must not be generalized to tasks whose center or tie semantics differ.

## Proposed nearest/farthest parameter prototype (review-ec54eded9d66352d)

This review adds a **proposed, unapproved** task-local prototype under
`workspace/parametric/`; production `generator.py`, canonical authority, catalog
approval, and training status are unchanged.

- Episode parameter: `selection_mode = nearest | farthest`, fixed for the whole
  episode. `nearest` is the exact canonical Racket source (SHA-256
  `1379212df45efd44f4bb6d4cafca92b9588442bfc83807ed5d926d3048ccade5`);
  `farthest` is one guarded, reversible `argmin` to `argmax` substitution
  (SHA-256 `01f1655af7c3e059e944456de586dee78c76a464f99595fb68a6af9e748fae55`).
- Paired seeds share inputs: even seeds select `nearest`, odd seeds select
  `farthest`. Defaults are 3 demonstrations and 4 distinct queries; each count
  is independently supported from 1 through 8.
- The sampler reuses the approved production input generator but rejects any
  candidate with a nearest or farthest distance tie. Every retained
  demonstration and query changes under the rival setting, so demonstrations
  alone identify the selected setting.
- Public files contain only demonstration inputs/outputs and query inputs.
  Opaque filenames are SHA-256 IDs of the exact visible bytes; seeds, settings,
  programs, provenance, rival predictions, and query labels remain private.
- `workspace/parametric/verify_evidence.py` independently checks manifest hashes,
  current prototype/verifier/generator bytes against retained snapshots, report and
  source bindings, public/private projection, all retained labels, rival behavior,
  and the canonical default via the bundled Racket runtime.

Changed-scope evidence: 37/37 prototype/verifier tests and 81/81 existing task tests pass.
The retained pair contains 14 Racket-replayed labels plus 4 canonical pairs;
the bounded adversarial pass also exercised 1-demo/8-query and 8-demo/1-query
boundaries, rejected source drift, duplicate public payloads and hash-valid
public tampering, and retained two concrete farthest-tie rejections. Evidence:
`checks/parametric/nearest-farthest-v1/` and `checks/parametric/adversarial.json`.

A pre-existing test-helper typo (`center2`) was repaired to `center` with a
hand-checked tie regression. This is test infrastructure only; it does not
change generator behavior.

Known limits: only the declared nearest/farthest family is analyzed; retained
runtime evidence covers paired seeds 0–3 rather than all seeds; ties are filtered
rather than taught; and the prototype remains outside production approval and
training admission pending maintainer review.

## Proposed bbox-anchor sibling

Retain selection_mode nearest/farthest and its strong evidence verifier unchanged; port midpoint/left_edge/right_edge as a sibling that always chooses the uniquely nearest marker. No anchor-by-selection-mode product is claimed.

Midpoint returns the exact canonical program; alternatives change only the bbox column expression. The independent component oracle and three authored Racket files are retained. The domain rejects ties under every anchor and requires left-edge and right-edge identifying demonstrations.

The sibling lives at `workspace/parametric/bbox_anchor/`, with its own adapter, bounded contract, and focused tests. It remains proposed and unaccepted, with `approved=false` and `training_admitted=false`. Production and the primary prototype code are unchanged. Current source identities, port decisions, prior/current evidence boundaries, and limits are in `evidence/conflict-reconciliation.json`.

Owner validation exercised 65 focused tests for this task (28 for the new sibling) in a relocated runtime; the combined two-task run passed 82 tests. The sibling's standalone 3-demo/4-query evidence used 21 protected Racket executions. These finite checks do not rerun the original reviewer batteries or approve a variant.

## D9. Promote the bbox-anchor family through the native root contract (review-2febf9404e8f55b2)

**Choice.** Make `workspace/parametric/adapter.py` the thin native adapter for the
existing `bbox_anchor` implementation. The private episode setting is
`anchor = midpoint | left_edge | right_edge`; `midpoint` remains the exact canonical
Racket source. Limit the native API to 2–6 demonstrations and exactly four queries.

**Why.** The retained anchor sibling already had an independent oracle, three actual
Racket programs, and constructive left/right teaching witnesses. Promoting it avoids
forking another implementation while supplying a meaningful input-dependent rule
parameter. The previous root nearest/farthest experiment remains historical evidence
and is not combined into a larger product family.

**Boundary extension.** Reserve one lawful 30×30 query in every episode. It contains
six separated rectangles (218 color-5 cells) with left, right, and bottom boundary
contact and remains anchor-sensitive. This extends only the parametric family; the
approved production distribution is unchanged.

**Sequential dependency.** Step A extracts each rectangle bbox and computes the
setting-selected anchor column. The intermediate is the per-rectangle bbox and anchor.
Step B consumes that value to select the unique nearest marker and its paint color.
The returned protected-Racket witness replaces the midpoint intermediate with the
left-edge intermediate and records a changed final output.

**Teaching scope.** The native worker fits all three declared programs to visible
demonstrations only. A bounded self-review additionally checks `rank_order` and
`vertical_overlap_only`. These finite rivals do not establish universal uniqueness.

**Status.** Reviewer-ready only after the returned manifest, qualification, public
projection, causal replay, and focused tests pass. Exact-source owner acceptance and
training admission remain pending and are not implied by this note.
