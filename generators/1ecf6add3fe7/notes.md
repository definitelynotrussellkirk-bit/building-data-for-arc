# Working notes: 1ecf6add3fe7

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current native extension: transfer the inferred pose
Keep the production generator and exact canonical rule unchanged. New setting
`response_policy=label_query|transfer_pose`: the canonical result supplies the
matched label and query occupancy. Infer the unique D4 mapping from that
prototype to the query, then apply it to the other prototype and render it in
the other label color at the query's bounding-box origin. Both prototypes have
equal area and equal ordered bounding dimensions but different D4 orbits;
both are asymmetric so all eight poses are distinguishable.

Plan: literal clockwise-transfer regression first; independently requested 2-6
teaching demos and 1-4 prefix-stable queries; one quarter-turn and one reflection
among the first two demos, with opposite match sides; executable fixed-pose,
inverse-pose, matched-color and recolor-only rivals; protected-Racket parity;
native inventory/qualification and source-bound wrong-intermediate witness.
The exact equal-panel geometry requires width 3*p+2, so the largest lawful
canvas is 30x29 (p=9), not 30x30. Stress will use substantive 27x9 asymmetric
shapes in all three panels rather than add an ignored thirtieth column.
Baseline collection also fails on a fixed-depth ledger path; replace it with
the portable helpers and resolve the archival authority path within that tree.

Self-review: the first two demos reject every declared rival under actual Racket
execution, without reading query outputs. All shapes have equal area/bounding
sizes and unique poses, and both matching sides appear. The first protected
seed pair covered seven orientation codes; added seed2 to the final bounded
audit to execute code6 as well. Final sweep: 20 seeds, 800 repeated count/setting
requests, 200 distinct inputs, 2,000 single-query projections, and 84 actual
protected Racket applications. All eight operations are exercised on lawful
smaller geometries; stress uses only dimension-preserving poses on 27x9 shapes.
Portable canonical/base-authority paths repaired without changing any test
assertion. Final code review is an author self-review, not independent review.
