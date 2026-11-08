# Working notes: cee14d35e7ec

## Review `review-1fdb7a258e5d0c5e` — 2026-09-28

The imported `1.1.1` generator was a fixed three-cell stencil. It always placed
three distinct colors at `(3,0)`, `(4,1)`, and `(n-1,2)`, so all sources were
below the diagonal and a position-specific or lower-to-upper-only shortcut fit
every generated example. Several declared axes were dead, singleton, aliased,
or silently ignored. The baseline battery failed lint, self-check power,
defect lint, canonical palette reachability, and the override contract; the
semantic gate was only advisory because no contract was declared.

Version `2.0.0` replaces that stencil with five observable scene profiles and
three honest axes. Every generated scene has 3–6 one-sided transpose pairs,
including a near-diagonal pair, a far pair, and an edge pair. A six-slot
schedule repeats the occupied-pair profile so every cyclic four-example lesson
contains both source directions and a different-color occupied pair. This
falsifies transpose-only, upper-only, lower-only, prefer-upper, and
prefer-lower shortcuts.

The canonical Racket rule was retained unchanged. All five canonical
train/test inputs pass the new structural checker, and the independent Python
mirror reproduces all five canonical outputs.

Evidence:

- Focused test: `4 passed`.
- Before battery: 5 failing stages (`lint`, `selfcheck`, `defect_lint`,
  `dist_gate`, `override`).
- After battery: all 12 stages green.
- Semantic gate: 600 inputs, all 5 witnesses firing, all 5 rival claims
  verified, and 12/12 four-demo lessons identifiable.
- Diversity: 300 pairs, 100% unique inputs and outputs.
- Override contract: 6,300/6,300 accepted draws, 70 cases × 3 bands, no
  findings; unknown keys rejected.

Intentional boundary: normal generation stays on 6–9 square grids with 3–6
one-sided source pairs and 3–4 nonzero colors. It does not attempt dense
arbitrary matrices. Lower-side, diagonal, and occupied-pair profiles are
rule-valid counterexamples used to identify preservation semantics beyond the
narrow official examples.
## Current reviewer considerations

Source SHA-256: `a6518d3abf8b7231b3fbf6266ef5090fdbf8a805af32169a2a85f6badaa18afa`.

# Design decisions: cee14d35e7ec

## D1. Keep the canonical Racket rule

**Original rationale:** unknown; the imported authority already contained a
compact conditional transpose fill.
**Alternatives:** replace it with an unconditional symmetrizer, transpose the
whole grid, or choose one side on conflicts.
**Probe:** an independent Python implementation matched all five official
outputs; authority sync and execution parity pass.
**Failure mode avoided:** unconditional or preference-based symmetry would
modify already occupied pairs, contrary to the existing `if current is blank`
condition.
**Limit:** the official examples contain only upper-triangle sources, so the
generator must supply lawful counterexamples to identify the full condition.

## D2. Reduce the public axis surface to three honest axes

**Choice:** `grid_size`, `source_pairs`, and `scene_profile`.
**Original rationale:** unknown. The old metadata listed `grid_h`, `grid_w`,
`palette_kind`, `anchor_corner`, `asymmetry_force`, `palette_size`,
`position_bias`, `n_distinct_colors`, and `texture`, but most did not affect the
returned grid or had singleton domains.
**Alternatives:** preserve diagnostic aliases or expose every internal random
decision.
**Probe:** the exact override matrix exercised 70 cases across three difficulty
bands and 6,300 accepted draws with zero findings; unknown keys are rejected.
**Failure mode avoided:** typoed or dead controls creating false confidence in
data coverage.
**Limit:** colors remain internal randomness because their exact identities do
not define a semantic branch.

## D3. Use square sizes 6–9

**Choice:** difficulty-aware draws over 6–9.
**Original rationale:** the official inputs are 6×6, 7×7, 8×8, and 9×9.
**Alternatives:** larger generalized squares or rectangular matrices.
**Probe:** all official inputs pass `self_check`; canonical profile floor is
60/60 inside the envelope.
**Failure mode avoided:** rectangular grids would make `(c,r)` undefined for
some cells under the selected rule.
**Limit:** the generator does not claim behavior outside the official size
envelope.

## D4. Vary one-sided source count from 3 to 6

**Choice:** 3–6 source pairs, with three guaranteed spatial witnesses.
**Original rationale:** the official rows use three or four sources; the old
generator fixed the count at three.
**Alternatives:** stay exactly canonical at 3/4, or allow dense arbitrary
counts.
**Probe:** default-cohort tests observe all four counts and at least 30 distinct
pair coordinates; the distribution gate matches canonical morphology.
**Failure mode avoided:** count-specific and fixed-position copying shortcuts.
**Limit:** 5/6-source rows are controlled extrapolations, not direct canonical
copies.

## D5. Guarantee near, far, and edge pair positions

**Choice:** every generated scene contains a distance-1 pair, a pair at least
half a grid from the diagonal, and a pair touching the top or right edge.
**Original rationale:** unknown; the baseline's three coordinates were almost
fixed.
**Alternatives:** unconstrained uniform sampling or fixed canonical positions.
**Probe:** focused tests assert all three witnesses for every explicit profile;
50 generated episodes yield 100% unique inputs.
**Failure mode avoided:** local-offset and three-coordinate lookup rules.
**Limit:** this is stratified random coverage, not a uniform distribution over
all unordered pairs.

## D6. Include five scene profiles

**Choice:** upper-only canonical, lower-only, mixed sides, diagonal context,
and occupied pairs.
**Original rationale:** the official examples show only upper-only sources; the
baseline instead showed only lower-only sources and no preservation contexts.
**Alternatives:** reproduce only the official orientation, or randomize all
cells without profile labels.
**Probe:** the semantic census sees all five profiles in every pooled run; all
five witness predicates fire.
**Failure mode avoided:** direction-only completion, transpose-only output, and
failure to preserve diagonal or occupied cells.
**Limit:** lower-only and mixed profiles are rule-valid extrapolations used for
identifiability.

## D7. Put two occupied-pair witnesses in that profile

**Choice:** one same-color occupied pair and one different-color occupied pair.
**Original rationale:** no original rationale; this branch was absent.
**Alternatives:** same-color only, different-color only, or no occupied pairs.
**Probe:** `prefer_upper_on_conflict` and `prefer_lower_on_conflict` are each
falsified in 60/60 rival checks.
**Failure mode avoided:** a model that forces all transpose pairs to one shared
value instead of preserving both existing values.
**Limit:** exactly two occupied pairs keeps observation and override recovery
unambiguous.

## D8. Repeat `occupied_pairs` in a six-slot lesson schedule

**Choice:**
`upper, occupied, lower, diagonal, occupied, mixed`, with
`EXAMPLES_NEEDED = 4`.
**Original rationale:** the old generator had no lesson schedule.
**Alternatives:** independent random profiles or a five-profile cycle with no
repetition.
**Probe:** every cyclic four-example window contains an occupied conflict and
both source directions; 12/12 sampled lessons pass `lesson_identifiable`.
**Failure mode avoided:** aggregate diversity that still materializes an
ambiguous four-demo training row.
**Limit:** the repeated profile deliberately overweights conflict preservation
relative to the official set.

## D9. Use three or four nonzero colors

**Choice:** three colors for three sources and four colors when four or more
sources exist; every chosen color appears.
**Original rationale:** the baseline always used three colors, while official
rows reach four nonzero colors.
**Alternatives:** arbitrary 1–9-color palettes or fixed official color IDs.
**Probe:** the distribution gate changed from
`canonical_palette_unreachable: gen=4..4 vs canon=5` to a pass at palette 5.
**Failure mode avoided:** a palette-size shortcut and unreachable canonical
marginal.
**Limit:** color identity is intentionally irrelevant; only distinctness and
coverage matter.

## D10. Make structural validation observable, not metadata-dependent

**Choice:** infer profiles from the grid and validate shape, size, source
count, color count, diagonal context, and occupied-pair structure.
**Original rationale:** the old checker only enforced squareness and color
range.
**Alternatives:** trust generation metadata or reject every noncanonical
configuration.
**Probe:** all five official inputs pass; 34/58 generic destructive mutations
are rejected; transformed outputs are not accepted as fresh inputs.
**Failure mode avoided:** a toothless checker certifying blank, duplicated, or
semantically collapsed inputs.
**Limit:** some generic mutations remain lawful members of the grammar and
should not be rejected merely because they changed the original sample.
