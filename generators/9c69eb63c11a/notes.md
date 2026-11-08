# Working notes: 9c69eb63c11a

## Current production decision (v2.2.0)

- Keep the canonical Racket rule unchanged (`e0d91c9e70a7`): select the median-area nonzero 4-connected blob.
- The old v1.1.1 generator silently emitted exactly three blobs even though its metadata claimed 3–5. With three blobs, “median” and “second-largest” are identical, so a solver could learn the wrong rule.
- Production now emits exactly three or five isolated, single-color blobs. Five-blob draws use exact areas `[1, 2, 3, 4, 5]`; three-blob draws sample three distinct areas from `1..6`. The 8×8 lower boundary remains constructive.
- Lessons use the fixed semantic schedule `five_blobs, five_blobs, three_blobs`. The earlier alternating `3,5` proposal was reversed because holding out the only five-blob item left some two-demo query rotations ambiguous. Every two-demo window of `5,5,3` retains a five-blob counterexample.
- Public controls are only `grid_h`, `grid_w`, `n_blobs`, and `palette_kind`. Retired alias/fixed controls and the no-op `texture=solid` axis are rejected rather than silently ignored. Seed, sample index, difficulty, and override scalar types are validated strictly.
- The executable semantic contract names `second_largest_object` as the rival, supplies a five-blob witness, mirrors the canonical rule in Python for tests, and rejects lessons whose labels or demonstrations fail to distinguish the rival.

## Verified limits and next useful extension

The supported production domain is deliberately compact: dimensions 8–14, blob counts 3 or 5, four recoverable palettes, and fixed five-blob areas 1–5. No claim is made for four blobs, larger odd counts, touching blobs, repeated areas, or multicolor blobs. A future extension should first add a packing proof and Racket-parity witnesses for a broader family of five-blob size sets; it should not weaken the `5,5,3` teaching certificate.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ef202a289f4b22f8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `1794fc06ad4bf9a57e0a8387346ad9ffae1610716dc79a0c309a21dbd2781def`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source d02eb5fd441bb8859feed336de3ffc13ad13eafc1d359c2c19ac5366f1b4edd1 truthfully implements3/5blob teaching profiles and removes unsupported/no-op controls; unknown/retired inputs reject. The median-versus-second-largest alias is distinguished by the5blob schedule. Reviewer-reported scoped checks and failed/timeout limits retained in evidence/repair-ec4a602a93402a2f/manifest.json and evidence/reported-support-limits-ec4a602a93402a2f/manifest.json. Explicitly resolves this historical audit only, with canonical rule unchanged and no owner rerun or variant admission.

### Assessment or prior finding

## 9c69eb63c11a

**Reproduced teaching/domain defect; source left unchanged.** The audited
generator SHA-256 is
`1794fc06ad4bf9a57e0a8387346ad9ffae1610716dc79a0c309a21dbd2781def`.
Its battery finished with 8 green, 1 advisory, and 3 failed stages (`lint`,
`defect_lint`, and `override`), under
`checks/audit/9c69eb63c11a/battery/`.

`AXES` advertises `n_blobs`, `palette_size`, and `n_distinct_colors` values up
to five, but a request for five of each still generated exactly three blobs and
three colors. The advertised 14×14 boundary is rejected by the internal 9–11 by
9–12 draw ranges, and an unknown `typo_axis` is accepted. Exact observations
are in `checks/audit/override_probe.json`. A 300-draw, 100-per-band probe found
three components in all 300 inputs (`checks/audit/distribution_probe.json`).

That restriction creates a canonical-compatible shortcut: with exactly three
distinct-size blobs, “keep the second-largest blob” is identical to “keep the
median-area blob.” The retained five-blob input has areas 1,2,3,4,5 and belongs
to the documented `n_blobs=3..5` axis, although the current hard-coded
`self_check` rejects it. Canonical Racket rule hash `e0d91c9e70a7` keeps the
area-three color-3 blob; the shortcut keeps the area-four color-4 blob. Exact
input, outputs, hashes, and supported apply command are in
`checks/audit/9c69eb63c11a/counterexample.json` and
`checks/audit/9c69eb63c11a/racket.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ef202a289f4b22f8-v0001/audit_assets.json), manifest SHA-256 `85b5995ed9c09e6cb4836c288a7d184428039c6c231fb16ae21d8fa91e47de75`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Reviewer-native parametric decision (2026-10-25)

- Added a native `selection_mode=median|second_largest` family. Median is the
  exact selected canonical program; the alternative changes only the rank index
  after the same component extraction and stable area ordering.
- Used five distinct-area components in every demonstration so the historical
  three-blob alias cannot survive. Inputs are setting-independent and each
  demonstration separates both programs without using query answers.
- Retained four distinct queries and added substantive 30×30 stress with object
  areas `[17,31,47,63,79]`. Both the 2-demo and 6-demo boundaries qualified on
  seeds 0 and 17 through protected Racket (32 and 64 evaluations respectively).
- The protected causal witness substitutes the median rank for a
  `second_largest` episode; Step B retains a different component and the final
  grid changes. Portable changed-target tests pass 62/62; public projection and
  first-turn privacy checks pass.
- Finite reviewer evidence does not perform owner acceptance or admit training
  data. Next action: integrate these exact sources, rerun native qualification,
  inspect the rank semantics/input grammar, then run owner `parametric accept`
  separately.
