# 4a8c7e2bad04

0-bg grid (size varies) with: (a) one QUERY object in color 8 (a random connected polyomino S); (b) one MATCH object in a non-8 color with the IDENTICAL shape S (same per-row column-offset signature); (c) 1-3 DISTRACTOR objects in other colors whose signatures DIFFER from S. All objects are 8-gap isolated. Rule: take the query's row signature, find the first non-8 object with the same signature, and crop to its bbox. Output = that crop (the match shape in its color). Output dims = bbox(S).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
