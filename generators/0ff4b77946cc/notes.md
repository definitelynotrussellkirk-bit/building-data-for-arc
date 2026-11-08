# Working notes: 0ff4b77946cc

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native repair and parametric authoring

- Repaired the native generator at version `2.3.0`: candidate shape sets whose canonical packed gallery would exceed the input/output width are rejected before placement, and `self_check` now reports the exact required packed width. The retained 8x11 clipping counterexample is rejected and ordinary deterministic generation remains non-lossy.
- Added native parameter `order_policy` with exact canonical default `size_desc` and alternate `largest_orientation`.
- The alternate is sequential: identify the largest object, measure its bounding-box orientation, select descending order for a wide/square largest object or ascending order for a tall largest object, then feed that order into the unchanged top-aligned gallery packer.
- The minimum two-demo lesson contains both orientation branches. Demo and query banks are disjoint; 2--6 demos and 1--4 queries are supported; the fourth query is 30x30.
- The bounded audit covers 16 seeds, both settings, every 2--6 demo count, and four queries: 160 episodes / 1,280 pairs, including 672 wide/square and 608 tall cases. This is finite authoring evidence, not universal uniqueness or learning evidence.
- Exact canonical source remains byte-for-byte bound in `workspace/parametric/canonical.rkt`; protected execution, promotion qualification, causal ablation, and public sequential exports are recorded separately under current evidence/checks.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d4d1ba4b22a1c6e5:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `fac3007a5bc632df244b6e2795441873040e239cddf95b89fd400fe0afda51a1`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by generator v2.3.0: generation now rejects selected shape sets whose bbox widths plus mandatory gaps exceed the canvas, and `self_check` reports the same invariant. The retained 8x11 counterexample is a focused regression and a 1,280-draw deterministic sweep confirms ordinary outputs fit.

### Assessment or prior finding

## 0ff4b77946cc

**Reproduced generator invariant violation causing lossy labels.** The generator
claims that total packed width fits the canvas, but neither construction nor
`self_check` enforces it. In a deterministic census of seeds 0–999 with
`sample_index = seed % 11`, packed width exceeded grid width in 389/1000 easy,
236/1000 medium, and 11/1000 hard cases.

Concrete case: easy seed 1, sample index 1 is an 8×11, self-check-clean input
whose four sorted crops require width 12. The authoritative Racket output clips
the last one-cell color-6 object completely: the input has one color-6 cell and
the output has zero. The full non-lossy gallery and authoritative clipped output
are recorded together in `checks/audit/0ff4b77946cc/counterexample.json`; the
supported rule application and source hashes are in
`checks/audit/0ff4b77946cc/racket.json`. This is inside the documented generated
domain, not merely a speculative extension. No audit-target source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d4d1ba4b22a1c6e5-v0001/audit_assets.json), manifest SHA-256 `58f2f31a8352579db784933cb96c50dcf63db86a470f82e7745df2ce2e9d3ff5`.
<!-- arcpuzzles-current-audit-assessment:end -->
