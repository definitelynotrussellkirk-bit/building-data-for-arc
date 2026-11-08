# cbbecffcd70e

0-bg grid (h~5-7, w~8-10) with 2-3 HORIZONTAL SOLID RUNS — each run is a single horizontal sequence of length L (3..min(w, 6)) of identical non-0 color C, placed at a unique row chosen from h rows without repetition, starting at a random column c0 in [0, w-L]. Each run uses a DISTINCT non-0 color drawn from {2..9}. No two runs share a row. Outside cells are bg-0. Rule (DASH EACH HORIZONTAL SOLID RUN — KEEP EVEN-INDEXED CELLS, ZERO OUT ODD-INDEXED CELLS): For EACH horizontal contiguous run of identical non-0 color C spanning columns [c0..c0+L-1] in a row: KEEP the cells at even RUN-RELATIVE positions (offset 0, 2, 4, ...) with their color C; SET cells at odd RUN-RELATIVE positions (offset 1, 3, 5, ...) to bg-0. Other rows and outside cells stay unchanged. Net: each solid horizontal stripe becomes a 'dashed' pattern of alternating color/zero cells starting with color at the run's left endpoint.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
