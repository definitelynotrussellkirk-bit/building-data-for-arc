# f8b9516df05e

Sparse 0-background grids contain 1–5 active rows. Each active row begins with one non-gray colored emitter and has a first gray (`8`) blocker to its right, separated by at least one empty cell. The rule fills only the empty cells strictly between emitter and blocker with the emitter color. The emitter, blocker, blank rows, leading background, and all cells after the blocker are preserved.

The v4 sampler is canonical-centred (mostly 8–10 rows, 9–11 columns, and 3–4 active rays) while exposing exact controls for `grid_h=5..14`, `grid_w=7..16`, `rays=1..5`, and `post_blocker_cells=0..3`. Every generated input contains a one-cell ray and trailing background after a blocker so that the declared `skip_unit_gap` and `ignore_blocker` shortcuts are executable and refuted.

Kind: `per_puzzle`. Selected version: `4.1.0`. Canonical rule hash: `d469cd5280c8`.
Approval is derived by the catalog from current code and retained evidence.

The v4.1 collision merge retains these exact controls and alternates canonical-capable draws with a separated second-gray-blocker witness. Each four-pair default window retains a first-versus-last-blocker counterexample after any single query holdout. Explicit `post_blocker_cells=0` remains legal; override-conditioned lessons need their own teachability check. Earlier solves and reviewer battery claims remain bound to their original v4.0 source bytes.
