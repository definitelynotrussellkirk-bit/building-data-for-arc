# e5477d32d98b

0-bg grid of 3 PANELS (each panel_w wide, panel_h tall) separated by single DIVIDER COLUMNS (color 5). panel0=BEFORE (a base shape in color A), panel1=AFTER (base + a connected DELTA of extra cells, color A), panel2=QUERY (the SAME base shape in color B). Rule: read the object in each panel; DELTA = cells AFTER has that BEFORE lacks (both normalized); output = the QUERY panel with DELTA painted in color B at the query's top-left. Net: before→after growth applied to query (before:after :: query:output).

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
