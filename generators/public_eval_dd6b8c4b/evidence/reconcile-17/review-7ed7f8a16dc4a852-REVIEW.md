# review-7ed7f8a16dc4a852 — two public-evaluation creations

Both assigned current-source families are reviewer-ready; neither is owner-accepted.
- `public_eval_db695cfb`: new general rule completes blue diagonal signals and lets on-signal red markers emit perpendicular beams; `both_edges` / `forward_edge` settings. All **6/6** supplied labels pass protected Racket.
- `public_eval_dd6b8c4b`: reconciled the proven maze-distance branch and retained `nearest` / `farthest` / `median_distance` collection settings. All **5/5** supplied labels pass protected Racket.
- Final local suite: **83/83 passed**. Relocated owner-layout replay: **76/76 passed** plus **34** protected-Racket evaluations.
- Current source-bound audits: **154** protected-Racket labels, **165** stress episodes, **365** count-prefix checks, and **40/40** sequential public views.
- Causal replays change **29** and **10** cells, respectively; both return `owner_replayed`.
- Cross-target review passed **420 episode requests** and **400 typed grids**, including maximum seed and 30×30 stress cases.
- Owner registration, source review, native qualification and fresh acceptance remain pending for both; `training_admitted` is false.

## `public_eval_db695cfb`

The canonical rule treats color 1 cells as endpoints of exact 45-degree signal
segments. It completes every such segment in blue. A color 6 marker is active
only when it lies on a derived segment; it then emits a perpendicular red beam,
with red painting last. The episode parameter controls whether that branch reaches
both canvas edges or only the derived forward edge.

The family supports independent 2–6 demonstration and 1–4 query requests,
setting-neutral matched inputs, stable prefixes and exactly four private queries.
The fourth query is 30×30 and distinguishes both settings. The minimum two-demo
prefix eliminates twelve retained alternatives, including connect-only, all-red,
no-connect, infinite-signal, wrong-color, wrong-trigger-count and wrong-direction
rules. An initially attempted full parallel-line variant was discarded because it
made several shortcuts structurally indistinguishable; the retained forward-edge
variant keeps trigger count, segment completion and direction observable.

The sequential dependency is source-bound: Step A derives complete segment cells
and signed orientation; Step B uses membership in that intermediate to gate each
red marker and uses the stored orientation to choose its branch. Replacing the
segment/orientation intermediate changes 29 protected-Racket cells.

## `public_eval_dd6b8c4b`

This current packet reconciles the previously built branch rather than rebuilding
it. The canonical rule computes four-neighbor shortest-path distances from the red
marker through non-wall cells, ignores unreachable maroon tokens, and moves the
nearest reachable tokens into the central 3×3 box up to capacity. Complementary
settings choose farthest tokens or tokens closest to the input-derived upper-median
distance. Current source hashes, immutable parent linkage and every authoring
receipt were regenerated or rechecked in this packet; reuse provenance is retained
at `checks/public_eval_dd6b8c4b/reuse-provenance.json`.

The minimum two-demo prefix distinguishes all three settings and rejects fifteen
retained shortcuts. Step A derives reachable geodesic distances and the median
when needed; Step B ranks reachable tokens under the episode policy and performs
the capacity-limited move. Replacing the median with minimum distance changes ten
protected-Racket cells.

## Evidence and limits

Each task contains `reference.rkt`, `generator.py`, focused tests, and
`workspace/parametric/{adapter.py,canonical.rkt,promotion.json,evidence/manifest.json}`.
`checks/TASK/preflight/` contains the current protected authoring receipt,
execution episodes and official-pair results. `checks/TASK/audit/` contains
current parity, finite-rival, source-bound causal, stress and sequential-public-
view evidence. `checks/relocation.json`, `checks/final-review.json` and
`checks/public-export-conformance.json` provide independent layout and cross-target
checks.

The packet's generic `check_first_turn.py` was also attempted and retained at
`checks/first-turn.json`; it exits before checking because it requires a private
`qualification.json`, which correctly does not exist before owner qualification.
The authoring audit and final review independently check first-turn/count
invariance, masking and exact visible-byte content IDs. No qualification file was
fabricated to satisfy the later-stage tool.

Finite rivals and bounded deterministic seeds are not a proof of universal rule
uniqueness. Final code review was an author self-review because no independent
reviewer subagent was available. Catalog task tests are unavailable before owner
registration; direct and relocated source tests passed instead.
