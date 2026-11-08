# Working notes: `2038a3a66886`

## Review finding

The selected `2.0.1` baseline described eight axes, but only grid dimensions and row count materially affected generation. `palette_kind`, `palette_size`, `n_distinct_colors`, `density`, and most `texture` values were dead or misleading; the module also lacked the canonical `RULE_HASH`. Its ordinary distribution contained only one same-color pair per active row, so every canonical demonstration and generated lesson supported at least two strong shortcuts:

1. fill between any row's outermost nonzero cells, regardless of endpoint color; and
2. change only rows containing exactly two equal nonzero cells.

The interrupted before battery preserved the failures under `checks/before/`: lint failed on the missing rule pin and defect lint reported the overlapping/dead texture domain.

## Implemented distribution (`2.1.0`)

The Racket authority is unchanged and pinned as `aefdabd461d1`. The generator now samples an order-independent subset of that rule:

- every repeated color occurs exactly twice;
- its endpoints have at least one interior blank;
- a row may contain one or two repeated colors;
- two spans in one row are disjoint;
- every ordinary draw contains at least one mismatched-color two-singleton decoy row; and
- every ordinary draw contains at least one row with two independent repeated-color pairs.

The six public axes are all observable and jointly constructive: `grid_h`, `grid_w`, `pair_rows`, `double_pair_rows`, `decoy_rows`, and `palette_size`. Canonical grid/palette signatures are heavily weighted but the complete documented domains remain reachable. Difficulty changes preferences, not the legal domain.

## Evidence

- Final generator SHA-256: `f64b6dbdc354a7682a4ccea749a856140717e30f442bcd30ef170fcb80d79547`.
- Required after battery: 12/12 stages green (`checks/after/`).
- Task-local regression snapshot: 38/38 passed (`checks/task-tests/`).
- Override gate: 26,460/26,460 accepted draws across 294 cases, 30 seeds, and three bands.
- Semantic gate: 600/600 strict-valid draws; each witness fired 600/600; both declared shortcuts were refuted whenever checked.
- Profile floor: 51/60 exact canonical-profile hits and 58/60 envelope hits.
- Lesson census: 300/300 lessons materialized, 1,200/1,200 unique inputs, zero ambiguity/errors; both rivals refuted in every lesson.
- Independent workspace audit: 512/512 unique deterministic draws, zero validator failures, zero missing witnesses, zero unrefuted rivals, and 5/5 canonical oracle matches.
- Exact Racket-backed witness: `checks/shortcut-witness/`.

## Deliberate limits

The generator does not sample overlapping/crossing spans, a repeated pair mixed with singleton colors in the same row, colors occurring more than twice, or vertical analogues. Those cases are excluded because the selected rule's sequential color updates can become order-sensitive outside the disjoint-span domain, and they are not needed to break the strongest canonical-fitting shortcuts. Finite declared-rival checks do not prove universal identifiability.


## October 3 overlapping review adoption

Accepted exact v3.0.0 from review-c88b79a930311a45. Adds triple occurrences,
multiple pairs and singleton distractors through a five-pattern curriculum.
Earlier v2.1.0 decisions above are historical; its bytes and approval remain
retained. Reported 39 tests and 300 lessons passed; no maintainer rerun.
## Current reviewer considerations

Source SHA-256: `5879bc93f3a5aac870bc2b4f50c919d7376ad66660374079d30a694dc1b3998a`.

# Decisions for `2038a3a66886`

## Authority and starting point

- **Rule authority:** kept the canonical Racket rule unchanged and pinned `RULE_HASH = "aefdabd461d1"`. Canonical examples, rule smoke, and Python/Racket checks agreed, so changing authority would have added risk without addressing the measured defect.
- **Prior-return lead:** none. I used the immutable packet baseline and reran the required before battery.
- **Baseline interpretation:** the primary failure was a dishonest/weak sampler contract, not incorrect output semantics. The old generator emitted essentially one clean repeated pair per active row and therefore could not distinguish the intended rule from strong simpler rivals.

## Public axes

I removed the old false or degenerate controls and retained only four exact, observable axes:

1. `grid_h` in 6–18;
2. `grid_w` in 9–22;
3. `rows` in 1–6;
4. `row_pattern` in the five semantic families.

Each value is constructively supported in every difficulty band. `observe_overrides` reconstructs these values from pixels, and task tests exercise every pattern in every band plus all numeric endpoints. Unknown keys, booleans passed as integers, out-of-range values, and invalid pattern names reject.

**Rejected alternative:** keeping cosmetic “texture” names or one-value controls for backward compatibility. They were not observable independent dimensions and had already triggered lint/defect-lint; preserving them would keep the contract misleading.

## Semantic row families

The five patterns are:

- `canonical`: one color occurring twice;
- `triple`: one color occurring three times;
- `multi_pair`: two colors occurring twice in disjoint spans;
- `distractor`: one singleton plus one repeated color;
- `combined`: one pair plus one triple.

This is the smallest set I found that directly separates the intended rule from the two strongest canonical-fitting rivals while keeping generation and validation simple. Ordinary sample indexes cycle through these five patterns. Any three consecutive cycle entries include a triple and either a second repeated color or a singleton distractor, so both rivals are falsified regardless of the lesson's start offset.

**Rejected alternative:** purely random independent pattern draws. It had acceptable marginal witness frequency but could assemble a whole three-demo lesson with no witness against one rival. The deterministic schedule gives a lesson-level guarantee rather than relying on pooled frequency.

**Rejected alternative:** only add triple occurrences. That refutes `exact_pair_only` but leaves the one-span-per-row/outermost shortcut untouched.

**Rejected alternative:** only add multiple pairs. That refutes `outermost_nonzero` but leaves the exactly-two shortcut untouched.

## Layout restrictions

Repeated-color spans in a row are generated disjointly, each with at least one zero gap. Singleton distractors are outside repeated spans. These constraints make the output independent of iteration order and permit a total validator and independent oracle.

**Rejected alternative:** overlapping repeated-color spans. The selected Racket program mutates an output row while iterating colors, so overlap can expose processing order. I did not broaden the domain into an authority ambiguity merely to add visual complexity.

## Canonical-scale anchoring

The sampler draws from all legal heights, widths, and row counts but heavily duplicates anchors from the five canonical `(height, width, active-row-count)` profiles. Canonical/triple cases use a distinct color per active row. Multi-color families reuse a shuffled two-color palette across rows.

The first implementation gave each rich row fresh colors. A focused profile run then produced only 11/60 canonical-envelope hits (18.3%), below the 25% floor, even though exact sizes were present. Root cause: palette cardinality grew with `2 × active_rows`, coupling semantic richness to a noncanonical palette. Reusing the same two colors across rich rows preserved every semantic witness and raised the final profile result to 42/60 envelope hits with exact support in all bands.

**Rejected alternative:** weaken or opt out of the profile gate. The warning correctly identified a real distribution drift; the distribution was repaired instead.

## Difficulty

Difficulty changes only the probability of canonical anchors, not the legal axis domain or rule. This prevents an exact override from being valid in one band and silently clamped or rejected in another. Easy emphasizes smaller profiles, hard emphasizes larger profiles, and medium is balanced.

## Semantic contracts and reusable probe

The generator declares:

- `strict_canonical_like` with `MIN_STRICT_FRAC = 1.0`;
- `SEMANTIC_WITNESSES` for mixed rows and triple occurrences;
- `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` for both rivals;
- `WITNESS_RIVALS` linking each witness to the rival it must refute;
- `schedule_profile` and `SCHEDULE_PROFILES` for observable branch accounting.

`workspace/reference_probe.py` is intentionally independent of the generator's label helper. It implements the row rule directly, validates canonical authority, verifies replay determinism, counts profiles/patterns, detects identity examples, evaluates declared rivals, and checks cyclic three-demo windows. This is the main tool built for future agents working on this task.

## Tests and failure-driven changes

The focused test suite was written around the desired contract before the generator rewrite. Its initial run had 28 failures and 9 passes, establishing that the tests distinguished the baseline from the intended repair. The final portable run passes 39/39.

Retained failure evidence includes:

- the complete before battery;
- the first post-rewrite profile-floor warning at 11/60 envelope hits;
- the final repaired profile result and full after battery.

I did not treat the initial long override run as a semantic defect: the complete rerun finished and covered 49,500 draws with zero findings.

## Limitations and failure modes

- Generated repeated spans never overlap; precedence/order behavior is outside the supported domain.
- All active rows in a generated grid share one row pattern, which simplifies lesson branch accounting but does not test within-grid pattern heterogeneity.
- Rich semantic families reuse two colors across rows to remain within canonical palette scale; a learner could notice that correlation, although it does not determine the output and disappears in canonical/triple families.
- Declared-rival and cyclic-window checks are finite. They establish that two strong canonical-fitting shortcuts fail, not that no unimagined rival exists.
- The production census tests consecutive three-demo lessons plus one query but does not rotate every pair into every possible query position. The task-local probe checks all cyclic schedule starts, partially closing that gap.
