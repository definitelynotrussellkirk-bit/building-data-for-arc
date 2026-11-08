# Blind visible-only solve — 51c5df6650a9

This is a concise reviewer-authored work log, not a captured token trace.
Earlier rule exposure: no. Reference consulted during this solve: no.
Only solve-blind/challenge.json and its rendered visible examples were examined.

## Observations and hypothesis
All three visible examples keep the canvas dimensions. The nonzero colors along
the top input row form an ordering key; the remaining cells of each color form
a shape. The output removes the key, translates the shapes without rotation,
and places their bounding boxes from left to right in key order. Each shape
starts at output row 1; the first bounding box starts at column 0; successive
boxes have one blank column between them. The shapes need not have equal widths
or heights. Input shape locations do not determine their output order.

## Revision 1
Implemented a general color-key parser and per-color bounding-box translation.
Zero gaps in the key are ignored. No task ID, query-specific positions, stored
answers, canonical helpers, generator imports, or reference code are used.
The first checker invocation is a genuine solve attempt. No artificial failed
revision has been manufactured. Validation is against all three visible pairs;
masked-query correctness is unavailable and will not be claimed.
