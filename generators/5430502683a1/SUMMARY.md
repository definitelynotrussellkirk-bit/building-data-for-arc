# 5430502683a1

On background 0, each of two to four foreground colors marks exactly two
endpoints. Every pair is horizontal, vertical, or 45-degree diagonal. Compare
the number of cells in each inclusive span, choose the unique longest, and
paint only that complete span in color 8 on a blank grid of the input dimensions.
The canonical Racket authority is unchanged; its hash is `182c38f86c20`.

Version: `4.0.1`. Kind: `per_puzzle`. `EXAMPLES_NEEDED = 7`.
Seven demonstrations plus one query use eight consecutive examples of the same
seed with stable controls. Repeated metric-gap contrasts, diagonal winners,
free spans, color ranks and scan ranks distinguish 29 declared rivals under
the tested production and single-pair query-holdout policies. This is finite
teaching evidence, not universal identifiability.

Exact controls: `grid_h` 8..16, `grid_w` 9..18, `pair_count` 2..4 in every band.
Input colors range over 1..9, including 8; palette/count stay fixed per seed.
Unknown or removed controls and invalid integer values fail explicitly.
See `notes.md`, `tests/`, and `workspace/README.md` for rationale and replay.
Approval is derived by the catalog from current code and retained evidence.
