# Post-repair visible-only solve

Task: 0d5077971eea. Earlier rule exposure: yes, from the generator review.
The Racket rule, generator, canonical helpers, earlier solution explanations,
and private labels were not consulted during this solve phase. The inputs and
visible outputs came only from solve/challenge.json after prepare completed.
This is an operational model-authored work log, not a token-level transcript.
This attempt is exposed; it is not a second blind solve.

## Revision 1 — attempted solution

The three visible pairs have sizes 7x9, 8x11 and 7x9. A row-by-row Python
inspection showed that changed cells are all 8s and acquire their row's first
cell color. The first cell and non-8 interior cells stay fixed. A header of
zero leaves the row's markers unchanged.

Specific visible checks:

- Train 0 row 4 has header 0 and a later color-1 spectator before two markers;
  the entire row is preserved. This excludes using the first nonzero cell.
- Train 0 row 1 has header 8, a color-1 spectator, and an 8 marker; all remain.
- Train 1 row 2 has header 3 and a color-5 spectator, with seven markers;
  the spectator remains 5 and all seven markers become 3.
- Train 1 row 7 demonstrates that the same action reaches column 10.
- Train 2 has transforming rows on both row parities, and a header-only row
  is preserved.

The attempted program implements row-header replacement with a zero-header
exception and a marker-only condition. It uses the full row width and creates
new rows. No intentional negative and no invented failed revision were added.
The query grids' dimensions are 12x10 and 7x9; their outputs remain masked.
