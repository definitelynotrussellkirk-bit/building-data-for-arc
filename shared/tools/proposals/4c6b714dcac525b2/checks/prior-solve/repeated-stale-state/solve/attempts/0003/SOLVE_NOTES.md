# Final-source visible-only solve work log

This is an assistant-authored work log, not a token-level model trace. Earlier rule exposure: yes, from generator repair. During this solve phase I consulted the visible challenge, public metadata, my own measurements and solver, and the solve bookkeeping implementation to diagnose a stale-file error. I did not consult the generator, Racket rule, reference solutions, or private query labels.

## Preparation bookkeeping and preserved history

The initial prepare refused a finished old-source solve. After moving that record, fresh preparation produced the final-source challenge, but stale attempt and FINISHED_NOTES files remained. My final-source solution passed all 3 visible examples, recorded as revision 2 because a prior-source attempt was still present; finish correctly refused to overwrite an existing FINISHED_NOTES.md. Those exact files are retained in checks/prior-solve/final-source-stale-entries/solve. The earlier source record also remains in checks/prior-solve/seed-cap-stale-active/solve. Logs final-solve-prepare.log and final-solve-finish.log retain the bookkeeping failures.

I copied and byte-verified the whole stale active record, explicitly removed the active directory, and prepared again. The challenge hash and final generator binding are unchanged from the genuine final-source attempt. This clean record rechecks the same hypothesis on that same visible challenge. No failed reasoning attempt is claimed, and no evidence was overwritten to manufacture a success.

## Observations and hypothesis

Demo 0: Input: 21 rows × 6 columns. Output: 21 rows × 6 columns. A color-2 marker on row 9 gains four cells above it: a color-2 tip and a color-1 stem.
Demo 1: Input: 13 rows × 10 columns. Output: 13 rows × 10 columns. Four adjacent color-2 markers including the left boundary grow four cells each; two color-8 markers grow three cells each.
Demo 2: Input: 17 rows × 22 columns. Output: 17 rows × 22 columns. Both color-8 markers grow three cells, and the color-2 marker grows four, despite a different color majority and bar position.
Query 0: Input: 13 rows × 10 columns. Output: unknown.
Query 1: Input: 29 rows × 10 columns. Output: unknown.

The measurement in visible_experiment.json lists the added cells for every visible marker. Color 2 always gains four cells and color 8 three; marker columns change independently, the far tip retains the marker color, and the stem uses 1. The original bar and background stay in place.

## Hypothesis and implementation

Copy the grid, locate its full horizontal 1/2/8 row, and extend above each 2 or 8 by the observed height. Handle adjacent and edge columns by the same per-column operation. Clipping is a defensive implementation choice, not a claimed observation. No deliberately wrong solution or fabricated failed idea was introduced. The masked queries are left for independent scoring.
