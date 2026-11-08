# Final-source visible-only solve work log

This is an assistant-authored work log, not a captured token-level conversation.
Earlier rule exposure: yes, from the preceding generator repair. During this fresh solve phase I read only the newly prepared visible challenge, its public metadata, and my own experiment. I did not open the generator, Racket rule, reference solution, previous solution explanation, or private query labels.

The first preparation attempt refused a stale active solve with a source-binding error. That finished intermediate-source record is retained in checks/prior-solve/seed-cap-stale-active/solve; the error is retained in checks/final-solve-prepare.log. I then prepared this new challenge from final generator 8c8516063ea26db20c415a47d8d48bf346bb100c64e419d30f3988effc3ccb04.

## Visible observations and hypothesis

Demo 0: Input: 21 rows × 6 columns. Output: 21 rows × 6 columns. A color-2 marker on row 9 gains four cells above it, with color 2 at row 5 and color 1 in between.
Demo 1: Input: 13 rows × 10 columns. Output: 13 rows × 10 columns. Four adjacent color-2 markers including the left boundary each grow four cells; two color-8 markers grow three cells. This supports independent per-column growth even with touching markers and unequal marker counts.
Demo 2: Input: 17 rows × 22 columns. Output: 17 rows × 22 columns. The two color-8 markers again grow three cells and the color-2 marker four cells, despite a different color majority and base position.
Query 0: Input: 13 rows × 10 columns. Output: unknown.
Query 1: Input: 29 rows × 10 columns. Output: unknown.

The explicit experiment in visible_experiment.json measures the added cells for every visible marker. Every color 2 has length 4 and every color 8 length 3. Only marker columns change. The original horizontal bar and background are preserved.

## Revision 1

Implement the observed independent rule: locate the horizontal row consisting of colors 1/2/8, copy the grid, and add a vertical extension above every 2 or 8. Extension lengths are 4 and 3 respectively; the far tip retains its marker color and interior cells use 1. Clipping is a defensive implementation choice and is not a new claim inferred from these examples.

No deliberately wrong solution or fabricated failed revision was created. The visible-example check will be used only to test this single genuine hypothesis. Query predictions remain independently unscored.

## Observed check result and stopping reason

Revision 1 returned exit 0, matched all 3 visible demonstrations, and executed on both masked queries. I stopped after this genuine successful visible check; I have no independent query correctness result. Earlier exposure is yes and reference consultation during this solve is no.
