# Working notes: 151f4dc0c08f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native repair and parametric authoring

- Repaired the native lesson validator in generator `1.4.0`: each ordinary lesson now contains a diagonal-only positive relation, plus an unrelated pair when three or more markers are present. This directly closes the retained row/column-only shortcut without changing the canonical task rule.
- Added native parameter `matrix_rule` with exact canonical default `pair_alignment` and alternate `anchor_component`.
- The alternate is explicitly sequential: build the row/column/45-degree alignment graph, compute the connected component containing the smallest-color marker, then emit the component-membership matrix.
- Authored demo and query banks are disjoint; 2--6 demos and 1--4 queries are supported; the fourth query is 30x30. Every authored case contains both a transitive extension and an isolated marker.
- The bounded audit covers 16 seeds, both settings, every 2--6 demo count, and four queries: 160 episodes / 1,280 pairs. This is finite authoring evidence, not universal uniqueness or learning evidence.
- Exact canonical source remains byte-for-byte bound in `workspace/parametric/canonical.rkt`; protected execution, promotion qualification, causal ablation, and public sequential exports are recorded separately under current evidence/checks.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f5d819ca91249c77:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `6de6229af69518502e8c5b1b5e30ab1e4a7f78633e902fc68abc74ccdbffa790`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by generator v1.4.0: `_teaches_relation` now requires a diagonal-only positive pair in every ordinary lesson and an unrelated pair for n>=3. Focused regression tests reproduce the old row/column-only shortcut window and verify the repaired lesson rejects it; the canonical program is unchanged.

### Assessment or prior finding

## 151f4dc0c08f

**Reproduced teaching defect.** Generator SHA-256
`6de6229af69518502e8c5b1b5e30ab1e4a7f78633e902fc68abc74ccdbffa790`
only requires a lesson input to contain some related marker pair and, for three
or more markers, some unrelated pair. It does not require any demonstration to
show that 45-degree diagonal alignment counts.

At difficulty `easy`, seed `0`, consecutive sample indices `5,6,7` all fit the
rival **same row or same column only; ignore diagonals**. The next generated
query, sample index `8`, contains two markers at `(1,1)` and `(2,0)`, a diagonal-
only relation. The intended output is:

```json
[[8,8],[8,8]]
```

while the rival predicts:

```json
[[8,0],[0,8]]
```

All four inputs pass the target `self_check`. The supported Racket apply command
replayed all four outputs under rule hash `a79ed999a8f5`; each matched the local
intended matrix. Evidence: `checks/audit/151f4dc0c08f/lesson_counterexample.json`
and `checks/audit/151f4dc0c08f/lesson-racket.json`. This is audit-only and was
not patched.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-f5d819ca91249c77-v0001/audit_assets.json), manifest SHA-256 `978eee9306fbefaa7f8c6f872725831c0dcd7ed007752eeeaf9a6e11a3cf3e84`.
<!-- arcpuzzles-current-audit-assessment:end -->
