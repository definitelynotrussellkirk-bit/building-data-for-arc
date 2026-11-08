# Final-source visible-only solve work log

This is an assistant-authored work log, not a token-level transcript. Earlier rule exposure: yes, from generator repair. During this solve phase I read only the visible challenge, public metadata, my own measurements and solver, and the solve bookkeeping implementation to diagnose stale files. I did not consult the generator, Racket rule, reference solutions, or private query labels.

## Preserved preparation history

The initial prepare rejected a finished old-source record. Subsequent preparations produced this final-source challenge, but stale attempts and FINISHED_NOTES.md reappeared across tool calls. Two checks of the same final-source hypothesis each passed 3/3 visible examples, while finish refused to overwrite the old finish snapshot. Those exact mixed-source directories are preserved under checks/prior-solve/final-source-stale-entries and checks/prior-solve/repeated-stale-state. The earlier-source finished record is retained under checks/prior-solve/seed-cap-stale-active. Failure logs remain under checks/final-solve-*.log.

For this clean record I verified an archive of all existing files, removed the active directory, and performed prepare/check/finish in one process. The challenge and generator hashes are identical to the previous final-source preparation. This is a bookkeeping retry of the same genuine hypothesis, not an additional independently conceived solution. No failed reasoning attempt is invented or hidden.

## Visible observations

Demo 0: Input: 21 rows × 6 columns. Output: 21 rows × 6 columns. A color-2 marker on row 9 gains four cells above it, with a color-2 tip and three color-1 stem cells.
Demo 1: Input: 13 rows × 10 columns. Output: 13 rows × 10 columns. Four adjacent color-2 markers, including the left boundary, grow four cells each; both color-8 markers grow three cells each.
Demo 2: Input: 17 rows × 22 columns. Output: 17 rows × 22 columns. Both color-8 markers grow three cells; the color-2 marker grows four despite the changed color majority and base row.
Query 0: Input: 13 rows × 10 columns. Output: unknown.
Query 1: Input: 29 rows × 10 columns. Output: unknown.

The measured additions in visible_experiment.json show color 2 consistently maps to length 4, and color 8 to length 3. Only marker columns change. The far tip keeps the marker color, the stem uses 1, and the original bar/background remain in place.

## Implementation and uncertainty

Copy the grid, identify the full horizontal 1/2/8 row, and extend above every 2 or 8 independently by the observed height. Adjacent and boundary markers use exactly the same operation. Defensive clipping is implemented but is not a conclusion inferred from these examples. This phase used one genuine rule hypothesis, repeated only because of the retained bookkeeping failures. No intentional teaching negative was presented as a natural failed attempt. Masked query correctness remains independently unscored.
