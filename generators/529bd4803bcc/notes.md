# Working notes: 529bd4803bcc

## Current rule and authority

Color 5 is an impermeable wall. For each 4-connected component of non-5 cells, count seed cells in colors 1, 2, and 3. Exactly one seed floods the whole component with that seed color; zero or multiple seeds clear to 0; walls stay 5. Canonical rule hash: `222cee10aaec`.

Generator version 3.0.0, final reviewed source SHA-256: `c599785ba7e3c2093bc835ec033d259570522eb82b69cc91662c9b1355bc1cc2`.

## Distribution decisions

- Regular scenes use unframed full gray row/column bands, matching canonical geometry.
- Every other schedule slot adds a local-only separator and forced label disagreement to refute “only global dividers matter.”
- Every default scene includes a three-seed negative, refuting the canonical-fitting odd-count shortcut.
- Exact observable axes: dimensions 10..18, row/column divider counts 1..2, wall thickness 1..2, regular/local layout, 0..3 single-seed chambers, and 2..4 seeds in the one multi-seed chamber.
- One regular slot in four is an 11×11 palette-5 anchor, guaranteeing canonical-profile support per band without fixing the rest of the size distribution.
- `self_check` is branch-neutral. `strict_canonical_like` separately identifies regular canonical-manifold scenes.

## Evidence

Final battery: 12/12 green at `checks/after-final/checks/529bd4803bcc_after_battery_summary.json`. Focused tests: 25/25. Large lesson census: 300 lessons / 1,200 unique pairs, 0 production and 0 rotated-query ambiguities against declared rivals. Minimal Racket-checked witnesses are in `counterexamples/canonical_shortcut_witnesses.json`.

## Known limits

The sampler covers rectangular global partitions plus one local straight separator, not arbitrary maze topology. Finite rival checks cover `odd_seed_count` and `global_dividers_only`; they do not prove universal identifiability. Catalog approval remains external to this review.
## Current reviewer considerations

Source SHA-256: `c599785ba7e3c2093bc835ec033d259570522eb82b69cc91662c9b1355bc1cc2`.

# Decisions — 529bd4803bcc

## D1 — Model walls as arbitrary 4-connected separators, not named frame templates

**Prior choice observed:** the baseline always drew an outer gray frame and one-cell cross/T/straight templates. Its rationale was not recorded, so the original intent is unknown.

**Decision:** use unframed full row/column wall bands for the canonical manifold and alternate a local-only wall segment inside one rectangle.

**Why:** the rule is component-based; named global templates make “partition only by full divider lines” a plausible shortcut. The local segment creates a minimal disagreement while the regular branch retains canonical morphology. Alternatives rejected: keeping the outer frame (noncanonical and unnecessary), or using arbitrary mazes everywhere (weak canonical support and harder lessons).

## D2 — Replace dead texture/palette controls with exact semantic axes

**Decision:** expose `grid_h`, `grid_w`, `row_dividers`, `col_dividers`, `wall_thickness`, `layout_kind`, `n_single`, and `multi_seed_count`, with strict domains and unknown-key rejection.

**Why:** every control is visible in the returned grid and recoverable by `observe_overrides`; the baseline texture variants were behaviorally dead and had overlapping domains. Joint extrema were tested in every difficulty band. No incompatible combinations are required for the published domains.

## D3 — Make validation branch-neutral

**Prior choice:** baseline `self_check` required at least two single-seed compartments and therefore rejected canonical train example 3.

**Decision:** validate only structural/task legality: rectangular ARC colors, walls, at least one seed, and at least two non-wall components. Keep stricter canonical-manifold checks in `strict_canonical_like` rather than treating a training preference as the rule.

**Limitation:** `self_check` intentionally accepts more lawful rule inputs than the default sampler emits; it is not a complete characterization of every sensible ARC scene.

## D4 — Teach the exact-count boundary with three seeds

**Decision:** default every multi-seed negative to count three while retaining exact overrides 2–4.

**Why:** all canonical multi-seed chambers have count two, so “fill iff the count is odd” fits every canonical pair. The three-seed witness makes that rival visibly wrong. The exact Racket-checked case is retained in `repo/generators/529bd4803bcc/counterexamples/canonical_shortcut_witnesses.json`.

## D5 — Schedule local-separator evidence every other sample

**Decision:** `schedule_profile` alternates `local_split` and `regular`; local scenes force one child of the split to contain a single seed and the sibling to be empty, with the multi-seed chamber elsewhere.

**Why:** merely adding a local wall would not guarantee a label difference. The forced placement makes the global-divider rival merge the two children and predict a different result. A four-pair lesson therefore contains two local and two regular scenes under every cyclic start.

## D6 — Add a deterministic canonical profile anchor

**Intermediate choice:** a 10/11-biased random size prior produced 7/60 pooled exact hits but medium happened to get 0/20.

**Decision:** sample indices congruent to 1 mod 4 use 11×11. These are regular odd slots whose three-seed negative cycles through colors 1, 2, and 3, guaranteeing exact profile `(11,11,5)`.

**Why:** per-band support should not depend on chance. Alternatives rejected: fixing half or all samples at 11×11 (unnecessary morphology collapse) and special-casing difficulty labels (the rule is difficulty-independent). Final floor: 19/60 exact, support in every band.

## D7 — Synchronize selected executable text without changing the rule

**Decision:** replace the selected base solution's comment-divergent `target_code` with the exact canonical `program_solution` text.

**Why:** authority sync requires exact active-source agreement. Raw/canonical behavior and normalized rule hash `222cee10aaec` were already correct; this is text synchronization, not a semantic Racket change.

## D8 — Lesson policy and limits

Training assembly checked here is four pairs per lesson with one production query; the large census additionally holds out each of all four positions. Production and rotation verdicts are both `no_ambiguity_found` over 300 lessons / 1,200 rotations against `odd_seed_count` and `global_dividers_only`. This finite declared-rival result is not a proof of unique induction against undeclared hypotheses.
