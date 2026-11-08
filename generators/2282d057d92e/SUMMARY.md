# 2282d057d92e

0-bg grid (h~6-9, w~9-13) with 3-5 ACTIVE ROWS (chosen randomly) each containing 1-3 SEED CELLS at distinct columns in DISTINCT colors from {1..9}. Each row may have multiple seeds (with 0-cell gaps between them). Edge case handled: if a row has only 1 seed at the rightmost column, a second blocker seed is added. Rule (CAST EACH SEED's COLOR RIGHTWARD UNTIL NEXT SEED OR BORDER): For EACH ROW r: WALK left-to-right. For EACH SEED at (r, c) with color C: PAINT every 0-cell to the RIGHT of (r, c) with color C, STOPPING at the next non-0 cell (another seed) OR the right border. Seeds preserved. Net: each row of seeds becomes right-flooding color rays separated by next-seed blockers.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
