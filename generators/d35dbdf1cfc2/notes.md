# Review notes: d35dbdf1cfc2

## Canonical defect and repair

The inherited `2.1.1` sampler used repeated random growth/placement attempts and, after exhausting them, returned the final grid without validating it. Its `self_check` only required two colors and six nonzero cells, so it accepted same-shape clones, touching motifs, split same-color components, and galleries that did not teach the size/rotation/sort law. A bounded probe found ordinary accepted scenes whose motifs all had the same size or normalized shape.

Version `2.2.0` is constructive. It places three to five 4-connected motifs at spread corner/center slots with a strict one-cell Chebyshev buffer. Generated scenes always contain at least two sizes and at least two normalized shapes; colors are distinct, controls are exact, and dimensions extend through 30×30. The validator separately preserves the official domain: canonical examples with all motifs size four remain valid, while malformed connectivity, repeated colors, touching motifs, invalid cell counts, and shape-clone galleries reject. The Python rule mirror crops each component, rotates taller crops clockwise, sorts by `(size descending, color ascending)`, and packs them with one zero column.

All five official pairs are accepted and reproduced exactly. A focused census generated 240 scenes (`3 difficulty bands × 80 seeds`) without fallback or retry shortening; every scene passed component, buffer, diversity, mirror, and cell-conservation checks. The exact 30×30 control case contacts the canvas boundary and spans at least 24 rows and columns. Unknown, coerced, out-of-range, and geometrically incompatible controls fail explicitly.

## Parametric motif-order prototype

`workspace/parametric/` adds one episode-fixed parameter:

- `size_desc` is the exact canonical Racket program byte-for-byte.
- `size_asc` reverses only the primary size comparator; color remains the ascending tie break.

Both settings retain component extraction, conditional clockwise rotation, crop packing, and one-column gaps. Every constructed demonstration has multiple sizes and a taller-than-wide motif, so it exercises both the rotation branch and the ordering decision. Each demonstration directly refutes the alternate setting. The adapter supports 2–6 demonstrations and independent 1–8 queries; the retained evidence uses three demonstrations and four distinct queries, including a boundary-spread 30×30 query. Generating one query or four queries produces the identical demonstrations and identical first query.

The bounded adversarial pass targeted the old weak-checker surfaces and the new export/count boundaries. Same-shape clone galleries and diagonally touching motifs now reject; all demo counts 2–6 identify the selected order; malformed settings, grids, and counts fail before partial episodes; private settings, program text, and query answers do not affect public challenge bytes or IDs. Protected Racket replayed two retained episodes, one per setting, for 14 label executions.

The native source/evidence manifest is current. Native owner qualification was attempted and correctly refused because the repaired production generator is not catalog-approved on its current source/rule binding. No catalog approval, variant acceptance, export publication, or training admission is claimed.
