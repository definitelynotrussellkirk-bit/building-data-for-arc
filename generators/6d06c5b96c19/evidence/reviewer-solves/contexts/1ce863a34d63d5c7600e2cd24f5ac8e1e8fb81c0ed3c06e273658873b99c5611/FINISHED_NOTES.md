# Blind solve work log

This is an assistant-authored work log, not a captured token-level model trace.
Only `solve-blind/challenge.json` was inspected. No generator, rule, notes, reference solutions, audit records, or private labels were opened, including the repair target's sources. Earlier exposure: no.

## Revision 1 — marker-controlled row rotation

The three visible outputs remove the first column. That column contains a repeated color and one exceptional cell. The two examples with the exceptional cell at row zero retain the remaining row order. The example with the exceptional cell at row one moves the last remaining row to the top.

Hypothesis: remove the control column and cyclically roll rows downward by the exceptional cell's zero-based row index. Detect the exceptional color relative to the majority control color, without depending on a fixed palette.

Visible probe: compare each trimmed grid and its possible cyclic row rolls with its provided output. Record all matching shifts and whether the inferred marker index agrees. A simple trim-only rule is contradicted by the third visible example. No deliberately wrong submission was created.

Limitations: the observed marker positions are only zero and one. The masked queries have positions one and three, so the larger shift is an extrapolation. Direction is determined by the third visible example. The current examples do not establish behavior for malformed control columns.

## Checker result and stopping reason

Revision 1 passed all 3/3 visible examples and executed successfully. The checker withheld masked-query correctness. Stopping with the single consistent rule; no hidden correctness claim is made.
