# Working notes: 61f255726e2e

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-02 — assignment review-a37191a18abd0395

Reviewer: Claude (Opus 5.5), an agent working from packet `4ed79512…`. Imported sampler 2.0.1, revised to 3.0.0. The canonical rule and its hash, `afb437709cc6`, are unchanged.

**Defect.** Every canonical bbox has a side of 2, so outline = filled bbox on all four canonical pairs (test `test_canonical_pairs_cannot_separate_outline_from_fill`). The 2.0.1 sampler drew 3–5-cell random walks, giving a 3x3 bbox in only 54–61% of grids. With three demos and one query, the demos had no hollow bbox while the query did in 46 of 900 Python-oracle lessons (11 easy, 18 medium, 17 hard, seeds 1000–1299). In those lessons, "fill the bbox" and "keep the blob and add its outline" fit every demo but answer the query differently. Six of nine declared axes were never read (`palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density`, `texture`). `n_blobs` came from an unkeyed `rng.randint`. The docstring said 8 axes and listed 9, and SUMMARY claimed a 1-cell padding check that did not exist. The `single_blob` and `bboxes_overlap` degenerate textures were not single 4-connected blobs, and the lint stage failed on the missing `RULE_HASH`.

**Repair.** Every grid has a hollow object whose blob crosses the bbox interior (a hub cell strictly inside, joined to an anchor on each side by monotone paths). Rivals are therefore refuted by every demo, not just by most lessons. After the repair, 0 of 900 Python-oracle lessons are ambiguous. Thin 2xk objects keep the canonical look. A second hollow object is an empty-interior perimeter arc half the time, which separates "fill" from "outline" without an erased cell. Placement is constructive backtracking with a background gap and a minimal-size fallback; all 32 corner combinations of the four axes pack on every tested seed. The axes `grid_h`, `grid_w`, `n_hollow` and `n_thin` are exact in every band and observable from pixels. Unknown, out-of-domain and non-integer overrides raise.

**Kept unchanged on purpose.**
- Distinct colors, with one component per color. Per-color and 8-connected readings of the rule are then extensionally identical to the canonical 4-connected per-object rule on every lawful input, so no lesson can teach the difference, and none needs to. Teaching it would need repeated colors plus a lesson-level guarantee that a demo shows them; I judged that a different task.
- Non-rectangular blobs: a solid 3x3 would also teach erasure, but canonical never shows one.
- Disjoint, separated bboxes: overlapping outlines depend on the prelude's row-major draw order, an undocumented tie-break.

**Open.**
- Thin-only grids (exactly canonical-looking) are no longer produced.
- The easy band still shows a hollow object in every grid, which makes it harder than canonical.
- Whether the hollow guarantee helps a trained model is not measured.
## Current reviewer considerations

Source SHA-256: `7df4d03e50dcc397b8a24b065239ba68fd6117bad80f59866da2d258d96eef2d`.

# Decisions — 61f255726e2e sampler 3.0.0

Each entry gives the choice, the original rationale (or unknown), the alternatives considered, the probe behind the choice, its failure modes and its limits.

## D1 — Every grid has a hollow object that crosses its interior

- **Choice:** at least one object with a bbox of 3x3 to 5x5 per grid. Its blob includes a cell strictly inside the bbox, which the rule erases.
- **Original rationale:** unknown. 2.0.1 drew 3–5-cell random walks, so hollow boxes appeared in only about 55% of grids, and only by chance.
- **Alternatives:**
  - A sample-index schedule (hollow on even indices). It guarantees identifiability only for consecutive-index lessons; mixed exports or `EXAMPLES_NEEDED` changes break it.
  - A per-grid probability (for example 70%). With p = 0.7, about 2% of lessons stay ambiguous.
  - Both rejected: the per-grid guarantee holds for any lesson assembly.
- **Probe:** `workspace/lesson_rivals.py --generator`. 46/900 ambiguous lessons before, 0/900 after; Racket-labelled audit in `checks/lesson-audit/`.
- **Failure modes:** a learner might come to expect a hollow object in every grid, which is a distribution cue rather than the rule. On canonical-style inputs with only thin objects the rule still applies correctly. Grids with only thin objects (exactly canonical-looking) are no longer emitted.

## D2 — Shape construction: anchors on all four sides joined to a hub

- **Choice:** one random anchor on each bbox side, joined by monotone lattice paths to a hub cell, plus up to two adjacent extra cells. The hub sits inside the bbox for the guaranteed hollow object. The result is 4-connected, touches every side (so the drawn bbox is exact) and is never the full rectangle.
- **Alternatives:**
  - Random-walk growth, as before: bbox size cannot be controlled and the walk can stall.
  - Plus/T skeletons only: they never produce the canonical S/Z shapes, while hub paths do.
- **Failure mode:** the path construction rarely leaves a hollow interior empty: 4/200 grids with two hollow objects did. Hence D3.

## D3 — Second hollow object is a perimeter arc half the time

- **Choice:** C, U, L or full-ring arcs of the bbox perimeter, which have an empty interior. Here the output differs from "fill the bbox" without any erased cell, so `outline_over_input` cannot be the only rival refuted.
- **Probe:** witness `empty_hollow` fired in 66/600 semantic-gate draws (easy 4, medium 15, hard 47).
- **Limitation:** a full ring is unchanged by the rule. It is lawful, but that object teaches nothing on its own.

## D4 — Distinct colors, one component per color, unchanged

- **Original rationale:** the INVARIANTS said "each blob has a distinct color"; the canonical pairs agree.
- **Consequence:** per-color bboxes and 8-connected objects give the canonical answer on every lawful input. The rivals `outline_per_color` and `outline_8conn` fit 300/300 lessons in each band, so they are equivalent here, not shortcuts.
- **Alternative rejected:** repeated colors and diagonal same-color contacts. They would teach the component notion, but a query with a repeated color is ambiguous unless a demo also shows one, which needs a lesson-level schedule (see D1). I judged that a different task from canonical.

## D5 — Separated, disjoint bboxes

- **Choice:** at least one background cell between any two bboxes. Overlapping outlines would depend on the prelude's row-major discovery order, a tie-break the task never demonstrates.
- **Limitation:** nested or overlapping objects are untaught.

## D6 — Exact axes, constructive placement, minimal fallback

- **Axes:** `grid_h` 7..14, `grid_w` 9..16, `n_hollow` 1..2, `n_thin` 0..3. All are exact in every band, because each band only reweights the full domain, as in `b90d4c3d5553`. All are observable from pixels.
- **Rejected:** `palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density` and `texture`. They were never read or were single-valued.
- **Placement:** backtracking with a 4,000-node budget, then minimal boxes (3x3 hollow, 2x2 thin) with a larger budget, then `RuntimeError`.
- **Test:** all 32 corner combinations (h ∈ {7,14}, w ∈ {9,16}, n_hollow ∈ {1,2}, n_thin ∈ {0..3}) × 4 bands × 15 seeds = 1,920 draws, each exact and lawful. The worst call took 6.6 ms; a default draw averages 0.17 ms.
- `INCOMPATIBLE_OVERRIDE_COMBINATIONS = []`: every combination is constructive.

## D7 — Canonical-profile core component in every band

- **Original rationale:** none. Iteration 1 failed the after-phase profile floor: the hard band had 0 canonical (h, w, palette) hits in 20 draws (`checks/after-iter1-profile-floor-fail/`).
- **Choice:** a `core` draw anchored on one of the four canonical (h, w, object-count) profiles, at 75% (easy), 50% (medium) and 25% (hard). Overrides still apply over the full domain.
- **Probe:** 400 pinned profile-floor draws per band give exact canonical-profile hits of 275 / 185 / 76.
- **Failure mode:** a quarter of hard-band grids are canonical-sized, which narrows the gap between bands. The gate requires this. Whether it is the right trade-off for training is untested.

## D8 — Racket rule unchanged

The written solution and the rule agree, and rule_smoke and authority_sync pass. Nothing in the audit suggested the rule was wrong. The tie-break for overlapping bboxes is undocumented but never exercised.
