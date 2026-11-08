# Working notes: 5e5205e54c96

## Production repair

The selected canonical corpus contains five labeled inputs. One official input
uses color 8 in the top-row legend. The prior validator rejected that input even
though the canonical Racket program deliberately excludes row 0 while discovering
color-8 frame objects. The production generator now accepts distinct nonzero
legend colors including 8, and deterministic ordinary sampling covers that case.
The stale fixed-15x15 summary was also replaced with the actual variable-size
nested-frame grammar.

## Native family

The exact canonical program is preserved byte-for-byte as
`ring_order=outer_to_inner`. The alternate `ring_order=widest_gap_anchor`:

1. sorts the rectangular color-8 frames outer-to-inner;
2. measures every adjacent four-sided inset and derives the unique widest index;
3. rotates the legend assignment so legend slot 0 fills the ring immediately
   outside that gap;
4. fills every annular interior using the resulting order.

Inputs are identical across settings, support 2-6 demonstrations and exactly
four queries, exercise anchors 0/1/2, include boundary contact, and end with a
substantive 30x30 query. The first alternate demonstration has a nonzero anchor.

## Evidence and limits

- 18 focused staged tests passed, including protected-Racket parity.
- 40 bounded audit episodes rejected the canonical competing mode and four
  declared shortcuts in every episode.
- The protected wrong-intermediate witness forces anchor 0 on an anchor-1 case
  and changes the final output.
- 16 public one-query projections passed verification; 4 first turns passed 24
  private-field invariance mutations and 4 visible-change controls.

These are reviewer-side authoring checks and finite declared-rival evidence, not
universal uniqueness, owner acceptance, or training admission. Exact-source
owner qualification and fresh acceptance remain required.
