# Working notes: bedcbc1cb6fb

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current separate parametric candidate

`workspace/parametric/` provides the exact canonical `rings` setting and a new
`ring_area_fill` setting. The latter fills the canonical nested rectangles,
measures the innermost color inside the completed frame, selects the unique
outside shape with that occupied-cell count, then completes its bounding box in
the innermost color. Both settings use identical input streams and protected
Racket labels. The selected production generator remains version 3.0.0, SHA-256
`893ce4c00ef7279f7318641b5c299e8cb04f67ce98da8e2a9ed436f5e50ec440`;
canonical full program SHA-256 is
`dc479cd51b3b078affe590a422cbc364d59a96b4cefd70df6982899af00aa1e9`.

The new grammar admits gapped diagonal markers and three nonrectangular outside
shapes, with colors disjoint from the marker palette. It supports 2–6 demos and
1–4 queries independently, defaults to 3/4, and includes a substantive 30×30
query. All inputs within an episode are distinct; count changes preserve
prefixes. The public projection reveals one query without count/future/private
metadata and hashes the exact bytes written. The writer rejects a nonempty
destination before generation or writes.

Initial short lessons admitted a three-marker truncation and numeric-color
shortcuts. The first two demos now contain three and five markers; the first
palette is nonnumeric. A bounded, demo-only selector checks the declared finite
rivals under both settings (64 candidates per demo, 128 total). An independent
review then demonstrated most-missing-bbox-cells and rightmost-key shortcuts.
Those findings are retained and now covered, along with the opposite hole and
coordinate extrema. No additional demos or query-answer-driven selection were
introduced. Diagnostics select layouts; only protected Racket supplies labels.
Because the same finite rivals are reused for selection and audit, the audit is
not an independent hypothesis census or a universal identifiability claim.

The sequential witness keeps the canonical frame result identical while
substituting another present key's area; this changes which external bounding
box is completed. Center area also has the equivalent direct formula
`(frame_height - 2*k) * (frame_width - 2*k)`. The claim is an input-dependent
geometric intermediate and lookup, not a requirement to literally paint first
or a proof of irreducible iterative simulation.

Assignment inspiration is public-evaluation `f560132c`, challenge SHA-256
`b141518eed470efcd0dba940f1cbf7e722b9f3c48eba852dc6432bb66df9cea6`.
The transferred idea is a compact visual key guiding reconstruction involving
separated monochrome shapes. Ring-area lookup is newly authored; verified
lineage, held-out answers, inherited difficulty and training admission are not
claimed. Private episode metadata retains `relationship_verified: false`.

## Evidence and next action

Source-bound current check summary and inventory live in
`workspace/parametric/evidence/`. The return's `checks/bedcbc1cb6fb/` retains
focused RED/GREEN tests, the initial literal Racket truncation reproduction,
independent-review counterexamples, finite self-audit, private four-query
examples, sampler/public-export probes, qualification and causal witness.
The adapter and promotion contract are a reviewer candidate: after integration,
the owner must qualify and accept the exact live source. No training activation.

## Production audit remains open

The retained `review-b2092a0c7f9fc0a3:v0001` audit identifies an off-domain
teaching limitation: row-major color collection and diagonal collection agree
throughout the calibrated production grammar; an off-diagonal distractor
separates them but is rejected by that grammar. This separate extension teaches
the distinction but does not modify production or resolve its audit status.
