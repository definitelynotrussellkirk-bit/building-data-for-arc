# Working notes: c2b9484357c1

## Review 2026-09-28 — review-be0df8e00cfebc38

Version 2.1.0 preserves the canonical Racket rule and changes only input construction plus declared semantic rivals/witnesses. The previous version passed the 12-stage battery, but all 512 sampled Racket-labeled targets had one hole. A single-hole-only selector, an outer-perimeter selector, and filling one hole of the correct winner fit all public and sampled baseline pairs.

The bbox-conflict minimum scene now has an 18-cell, 20-area, 14-rim two-hole target against a 16-cell, 24-area, 16-rim single-hole rival. Optional solid size is 24. Row/column duplication varies actual geometry, with a 24-attempt bound and valid-base fallback. Input-observable profile inequalities, unique target and larger solid are checked after each proposal. Slot-zero strict anchors retain thin frames.

Matched seeds 0–31, indices 0–3, and four difficulty settings produce 512 pairs per version. Every label comes from canonical Racket. Revised shape-multiset counts are 57/19/60/82 (None/easy/medium/hard), versus four throughout before. Two-hole winners occur 25% of the time; strict canonical-like examples remain 25%. No mirror/reference mismatch was observed. All 11 declared rivals have disagreements in each revised band; this is not proof against undeclared shortcuts. Both full batteries have 12 green stages.

Actual public-runtime episodes with three demos, medium, seeds 17 and 18 are ambiguous; the three rivals named above plus bounding-box selection fit demos and fail the held-out fourth profile. The returned emitted-lesson tool rejects both three-demo episodes and accepts both four-demo counterparts. Shared export wiring is not included. Do not consume this task's default three-demo exports without an actual episode contract check.

The direct task suite has 288 passing cases, including the original six assertions, 256 boundary combinations, geometry/multi-hole/perimeter regressions, transformation checks and tool contracts. The separate repository suite reports 130 pass/2 timeout-related failures in unchanged shared checker tests; timing-sensitive diagnostics do not convert that run into a pass.

Limitations: four topology backbones, small minimum dimensions, conditional-sampling bias and duplicates. More colors or raw unique grids are not independent task structures. No Qwen training was run; no approval flag was raised.

See `workspace/README.md` for exact usage. The review return contains the full evidence and detailed decisions. Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `7eefd49b0b144b1362b42d855fab254c80f801c14c7f701680dc6131ff14bb62`.

# Input and implementation decisions

Task `c2b9484357c1`; assignment `review-be0df8e00cfebc38`.

## Rule and authority

**Keep the canonical Racket rule.** The public examples and both matched Racket campaigns support its existing interpretation: select the uniquely largest hollow component by colored-cell count and fill every enclosed zero region of that component. The baseline issue was missing witnesses, not incorrect reference labels. A Python mirror remains a checked convenience for fast unit tests, never the label authority in the distribution campaign. Rewriting the canonical program would create unnecessary semantic and approval risk.

## Candidate count and object grammar

**Keep two hollow candidates in ordinary generation and at most one solid rectangle.** The existing v2 notes explicitly used competing candidates to make “largest” observable. The public grammar also permits the one-hollow canonical example. Retain complete rectangular outer perimeters, one or two holes, unique sizes, distinct component colors, and no foreign cells inside an object's bounding box. Alternatives include more candidates and arbitrary polyominoes, but those require stronger packing and reference-domain analysis. They are not needed to falsify the reproduced shortcuts.

## Multi-hole target

**Change the existing bbox-conflict profile, not the lesson length.** Its minimum witness is a 4×5 filled rectangle with two separate singleton holes: 18 colored cells. A 4×6 thin frame has 16 cells but a bigger box and longer rim. The target is therefore selected by actual colored-cell count. Previously multi-hole objects only lost the selection contest; this left the “single-hole objects only” and “fill one hole” hypotheses completely viable.

An additional fifth profile would preserve the old four exactly but increase demonstration requirements, worsening the already-observed export truncation defect. Reducing the lesson to three profiles would risk dropping existing first/last and hole-count witnesses. Combining the new evidence into the existing fourth profile preserves the contract and addresses several shortcuts at once. The full boundary cross-product checks that all overrides still fit the minimum canvas.

## Geometric variation

**Use keyed monotone row/column duplication.** The old orientation/color/embedding transformations changed raw grids without changing their four shape multisets. Duplication varies heights, widths, wall thicknesses and hole shapes while preserving connectivity and enclosedness. This is a local change with no new public axis and no dependency.

Unconditional duplication can reverse which component is largest, erase the intended bbox conflict, or make the solid decoy smaller than the target. Therefore candidates are accepted only when the selected profile, unique winner, and decoy inequality remain observable. The new bbox profile additionally requires the rival's outer perimeter to exceed the target's. Acceptance predicates inspect input structures; they do not compare output labels from a Python oracle.

Twenty-four attempts bound runtime. The known-valid base is the fallback. The exact value is a bounded practical choice, not a tuned optimum. Rejection and fallback can bias geometry frequencies; fallback frequency was not separately measured, and the design does not claim uniformity. A procedural arbitrary-mask generator could diversify topology further, but would be a larger and less readily verified change.

## Dimensions and orientation

**Keep height 8–12 and width 9–14.** The four backbones and optional solid all fit 8×9. The existing per-band choices and canonical-anchor dimensions are retained. Orientation is selected before geometric expansion so transposed scenes are stretched against the correct available dimensions. Horizontal reflection is only used in the original vertical layout to preserve scan-order profiles. Full min/max combinations over difficulty, dimensions, profile, solid inclusion and palette produce 256 test cases.

The minimum canvas has little spare geometric capacity. Broadening dimensions to all ARC bounds would produce easier apparent diversity without establishing task usefulness. That alternative was not adopted.

## Palette and background

**Keep background zero, distinct object colors, and the existing canonical/broad palette schedules.** Zero encodes holes in the reference domain. Distinct colors make components separable even when different colored shapes touch. Canonical colors remain {2,3,4,5}; broad colors {1,6,7,8,9}. A nonzero bijection test checks equivariance of the rule mirror. Making background an arbitrary color would change the zero-hole premise and was rejected. No new palette-derived shortcut was established in this review.

## Strict anchors

**Keep the 25% strict canonical-like floor.** The original rationale was maintaining recognizable public-style examples while introducing contrastive witnesses. Slot zero remains the strict anchor. Its stretch candidates must keep hollow objects as thin perimeter-only frames. This constraint reduces easy-band diversity but retains compatibility. Both Racket campaigns observed exactly 32 strict examples per 128-example band.

## Four-demo schedule

**Retain the existing schedule and expose its export precondition.** It supplies aligned-first, aligned-last, hole-count-conflict and bbox-conflict scenes. Its fixed order is not a claim of an optimal curriculum. The public exporter defaults to three demos, so changing geometry alone cannot make export safe. A task-local gate checks the actual resulting episode, not just its demo count. Shared pipeline edits were explicitly out of scope; an explicit four-demo export plus this gate is the supported research workflow in this return.

## Rivals and measurements

**Add three canonical-consistent hypotheses, not arbitrary hard adversaries.** All three fit every public pair and the entire matched baseline sample; each now has 32 contradictions per band. Existing rivals remain. This tests a concrete missing distinction rather than declaring improvement from more randomness alone.

**Report a coarse shape multiset alongside raw uniqueness.** Normalize each component under translation and dihedral transformations and forget colors and scene placement. This deliberately conservative diagnostic shows actual geometry changes, but can merge strategically different scenes in other ARC tasks. It must not be used as a universal split key or proof of independent examples. Hard-band raw uniqueness fell from 128 to 126 despite the large geometry increase; both results are reported.

## Tool contracts

**Validate private labeled episodes after Racket verification.** The gate checks every query, binds generator and rule provenance, detects input mutation, and treats missing hooks as “no contract.” It does not execute a second labeling oracle, recover absent test outputs, or elevate approval. It loads only explicitly supplied trusted local implementations; wrong-library runtime/module resolution is rejected. Repeated CLI invocations use fresh Python processes. It is not a sandbox for untrusted code.

Missing or inaccurate rival implementations can cause false positives. Adopt a shadow/quarantine rollout for other tasks until their contracts are vetted. Absence of known rivals cannot establish global identifiability.

## Validation friction and stopping

The old assigned tests could not import directly in the library. Their original assertions were retained and only source/authority path resolution was adapted. The first probe also exposed the inherited rule wrapper's staged `scripts.comment_solutions` import assumption; the local tool now maps that namespace to this library's own shared tools. Original failed runs remain as evidence.

No Git metadata was included in the packet. The immutable assignment snapshot provides the baseline; the supplied builder creates the deduplicated source patch and checks every untouched shared source. No destructive reset or repository-wide rewrite was needed.

The full repository test command was run and reported, not replaced by the passing task suite. Two unchanged short-budget subprocess tests timed out. Diagnostics indicate timing sensitivity, but the full suite is still recorded as failed. That issue is handed back as shared tooling feedback rather than altering tests outside the allowed scope.

The scoped work ends with implemented generator changes, runnable gates, positive and negative evidence, the two assigned audits, and a compact source-bound return. It does not claim measured model-training benefit, universal shortcut elimination, or production approval.
