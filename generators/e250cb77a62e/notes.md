# Working notes: e250cb77a62e

## Current native stamp-region build (review-235c7c2a314684f0)

The production version 4.0.0 and its exact canonical Racket authority are
unchanged. Native `stamp_policy=all_stamps|largest_joined` is implemented in
`workspace/parametric/`. First perform the canonical pattern stamping, then
measure four-connected cyan regions and recolor the unique largest green.
The intermediate is created by exact stencil contact/overlap, not by orange
anchor proximity or prototype bounding boxes. The alternate setting preserves
all nonselected stamps and the source frame.

The separate native grammar extends canvases to 30x30, uses more anchors, and
allows controlled contact/one-cell overlap; all footprints fit and avoid the
source frame. It deliberately does NOT modify the production sampler's old
1..4-seed/disjoint/11..22 contract. Minimum sampled size is 18x18. The final query
is a substantive 30x30 stencil scene with fourteen anchors and full boundary /
quadrant coverage. Shapes are a procedural staircase subfamily with variable
branches, not arbitrary connected shapes.

Self-review found a real two-demo shortcut: both original winners had exactly
two copies. The executable exactly-two-prototype-area rival fit both demos but
failed a larger query. The second demo now has a three-copy winner, retaining
the two-demo minimum. Minimal protected before/after cases and six executions
per version are retained at checks/e250cb77a62e/two-copy-before.json and
checks/e250cb77a62e/two-copy-after.json. The rival is in the reusable audit bank.

20 task tests plus 12 subtests pass after repairing legacy canonical-data path
resolution with reviewer_support. One inherited GenCtx._drawn deprecation warning
remains; assertions were not weakened. The final 20-seed audit covers 800 count /
setting requests, 5,200 pair instances across prefixes (175 distinct inputs),
400 matched-input comparisons, 2,000 masked public projections, 140 protected
Racket evaluations and ten executable hypotheses, with no remaining finite-rival
findings. A first combined command exceeded the outer deadline; its partial audit
directory is not a passing receipt. The completed rerun is audit-final/.

Source inventory, qualification/execution and a source-bound protected causal
witness are separate artifacts. Owner exact-source acceptance and any training
admission remain pending. Review was by the author, not an independent reviewer;
bounded seeds/rivals do not imply universal uniqueness or training benefit.

Owner reconciliation: Exact disjoint rules share matched inputs; selector sizes and positions vary across demonstrations, queries and seeds. Supports the declared demo limits, four prefix-stable queries and substantive 30x30 scenes. Original samplers remain task-local. The exact prior programs and incoming alternate are preserved. Fresh source-bound acceptance and causal evidence: `evidence/owner-variant-reconciliation/current.json`.
