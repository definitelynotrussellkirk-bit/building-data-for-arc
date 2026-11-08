# Working notes: 49f2e1c9f51a

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric review `review-417cd9039300ee73` — nearest/farthest barrier pivot

The production generator and canonical authority remain unchanged. The task-local
native family preserves the canonical `nearest` program byte-for-byte and adds a
matched-input `farthest` setting. Both rules scan the target-facing source ray,
select a barrier, retain the barrier-adjacent pivot, and then consume that pivot
to route the remaining two orthogonal legs to the red target. The alternative
changes only first-versus-last barrier selection; it does not simplify the route.

The family supports 2–6 demonstrations and 1–4 independently revealable queries.
Its ten deterministic profiles cover both orientations and directions, three
separated ray barriers, later-leg distractors, broad canvas sizes, and a substantive
30x30 boundary case. The first two demonstrations distinguish the settings and
seven finite rivals: middle barrier, border pivot, after-barrier pivots, target-axis
turning, and missing red restoration. A seed-15 collision found during self-review
was repaired by preventing the authored farthest pivot from collapsing to the
border pivot. The optimized sweep then passed 256 seeds without a teaching collision.

Exact hashes: production generator
`125ee9cdf5665f25ed334b54290c741f68605508b38fc543a0844d8ad80286e9`,
canonical program
`856dec5bf62bfee9d04b5f753a3a575e3943215398df7889a24a4e6ecea535d1`,
and farthest program
`bbe0c443c070aca437e7e2b2df55f711a7b2cdfe8832e583626dc50146832c8f`.
The protected audit executed 40 labels over 12 setting/prefix jobs, made 308
named-rival checks, validated 16 public projections, and found zero failures.
Native qualification passed all four setting/seed jobs. The standardized witness
changes 56 final cells when the qualified farthest pivot is replaced by the
nearest pivot.

The copied-runtime canonical test was made portable by replacing its fixed checkout
depth with `reviewer_support`; no production behavior changed. Finite rivals and
seeds do not prove universal uniqueness. Owner integration, fresh exact-source
acceptance, and any training admission remain separate and were not performed.
