# Working notes: a4a506dda35f

## Intended rule

Count all non-background cells by numeric color. Sort `(color, count)` entries
by count descending, breaking equal counts by smaller numeric color. Emit a
single row with each color repeated by its count. The selected canonical Racket
rule already implements this correctly and was not edited. `RULE_HASH` is pinned
to `639443b5cb4a`.

## Review finding and reversals

The imported `2.0.1` sampler deliberately used only isolated cells and strictly
distinct counts. That made two wrong rules fit every canonical demonstration:
counting connected components instead of cells, and breaking equal counts by
row-major first appearance. It also advertised controls it did not consume,
used smaller-than-canonical canvases, rejected the canonical tied-count example,
and returned invalid advertised degenerate textures.

Version `3.0.0` reversed the “avoid ties / keep every occurrence isolated”
choice. A final independent review then found that its fixed count signature per
layout made `(shape, palette)` determine the output, permitting a 24-case lookup
instead of counting. Version `3.1.0` removes that new shortcut by varying both
the frequency signature and its assignment to colors independently of layout
and palette.

The ordinary curriculum now:

- cycles through six fixed layout profiles, including all four canonical shape
  families plus two four-color extensions;
- uses four exact, independently observable palette profiles;
- samples one of several lawful tied/distinct count signatures and a permutation
  assigning those counts to colors, independent of shape and palette;
- puts an adjacent same-color pair in every draw, so component count disagrees;
- places the numerically larger tied color first on tied profiles, so a
  first-seen tie break disagrees with numeric ascending order;
- gives each four-pair lesson at least one remaining tie witness under every
  query rotation;
- uses separate deterministic placement streams for `None`, `easy`, `medium`,
  and `hard` without changing the task grammar.

Across the four palettes, supported three-/four-color tied and distinct
frequency assignments produce exactly 552 lawful output bars;
`EXPECTED_OUTPUT_CODOMAIN = 552`, and the focused test exhaustively enumerates
the declared support. `checks/anti-lookup-witness.json` retains two generated
inputs with identical shape, palette, tie mode, and total painted-cell count but
different correct outputs.

## Contract and evidence

`strict_canonical_like`, `observe_overrides`, `SEMANTIC_WITNESSES`,
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`,
`WITNESS_RIVALS`, and `lesson_identifiable` are executable. The declared
shortcuts are checked against all five labeled canonical pairs. Retained exact
reproducers are:

- `counterexamples/component_count_sort.json`
- `counterexamples/first_seen_tie_break.json`

Focused tests are in `tests/test_generator_a4a506dda35f.py`, including explicit
regressions against profile lookup and fixed numeric-rank frequency assignment.

## Limits and open scope

The strict sampler domain is intentionally narrower than the total Racket rule:
it supports six shapes, three or four nonzero colors, per-color counts `1..4`,
and outputs no wider than the input. The 552-label support is still finite, and
the finite rival set proves only that the declared shortcuts are distinguished;
it does not prove unique induction over all conceivable programs. Difficulty
changes placement streams, not semantic complexity. No prior repair return was
used as a patch; the current packet's canonical data, baseline source, shared
contracts, and battery evidence were the inputs to this review.
## Current reviewer considerations

Source SHA-256: `cef796910334f52262e46b1171e52ab6cbcef8e16ec870b1ef4b2dc0ef04584f`.

# Decisions — a4a506dda35f

## D1 — Keep the selected Racket authority unchanged

**Original state.** The baseline sampler was defective, but the selected Racket
rule matched all canonical labels. The original rationale for the sampler's
narrow distribution was not recorded.

**Choice.** Pin `RULE_HASH = "639443b5cb4a"` and leave canonical/base rule bytes
unchanged.

**Alternatives rejected.** Rewriting the rule in Python or editing Racket to
match the sampler would weaken the authority and hide the real issue.

**Probe/evidence.** Before and after `rule_smoke`, `racket_lint`, and
`authority_sync` passed; the final battery is 12/12 green. The question witness
was also executed through supported `arcpuzzles apply`.

**Failure mode/limit.** This does not prove behavior on every total-rule input;
it establishes canonical and sampled parity. A latent rule-domain issue would
remain outside the selected sampler.

## D2 — Replace eight misleading controls with two exact controls

**Original state.** `grid_h`, `grid_w`, `palette_kind`, `n_colors`,
`palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`
were advertised, but several were ignored, coerced, dead, or could request
invalid degenerate outputs.

**Choice.** Expose only `layout_profile` and `palette_profile`; validate unknown
keys and values strictly, consume both through `GenCtx`, and recover both from
returned grids via `observe_overrides`.

**Alternatives rejected.** Retaining aliases for compatibility would preserve
ambiguous controls. Supporting arbitrary dimensions would add packing and
profile complexity without teaching another rule branch.

**Probe/evidence.** The focused suite exhausts all 6 × 4 joint profiles in all
four difficulty settings, rejects invalid scalar/override requests, and the
final override stage passes.

**Failure mode/limit.** The advertised domain is intentionally finite; callers
cannot request arbitrary dimensions, counts, or palettes.

## D3 — Use six scheduled layout profiles

**Choice.** Cycle through four canonical-size three-color profiles and two
larger four-color extensions:
`7x9 tie`, `7x10 distinct`, `7x11 tie`, `8x10 distinct`, `10x14 four-color tie`,
and `9x12 four-color distinct`.

**Rationale.** This restores every canonical shape/palette profile, keeps
outputs within the input width, alternates tie/distinct semantics, and adds a
controlled four-color extension.

**Alternatives rejected.** Pure random dimensions missed canonical support;
canonical-only shapes would teach less compositional breadth; an all-tie or
all-distinct curriculum would leave one ordering branch weak.

**Probe/evidence.** `profile_floor`, `dist_gate`, grammar, and the exhaustive
focused schedule test pass. Every 24-draw band sample covers all profiles.

**Failure mode/limit.** The strict manifold does not cover all legal Racket
shapes or arbitrary color cardinalities.

## D4 — Force a cell-count versus component-count witness on every draw

**Choice.** Place at least one adjacent pair of the dominant color in every
ordinary example.

**Rationale.** All canonical colored cells are isolated, so counting components
per color fits every canonical pair. Adjacency makes occurrence count and
component count disagree without changing the intended rule.

**Alternatives rejected.** Merely declaring the rival, or emitting the witness
rarely, would permit ambiguous lessons. Large solid regions would introduce an
unnecessary morphology bias.

**Probe/evidence.** Exact retained counterexample
`counterexamples/component_count_sort.json`; focused independent rival test;
100/100 lessons per band refute the rival in the census.

**Failure mode/limit.** This distinguishes 4-connected component counting; it is
not a proof against every possible grouping heuristic.

## D5 — Teach numeric tie-breaking explicitly

**Choice.** On alternating profiles, give two colors equal counts and place the
numerically larger tied color at the first painted cell. The intended numeric
ascending tie break therefore disagrees with a row-major first-seen tie break.

**Alternatives rejected.** Strictly distinct counts reproduce the baseline
blind spot. Random tie placement could accidentally agree with first-seen order.

**Probe/evidence.** Exact retained counterexample
`counterexamples/first_seen_tie_break.json`; all canonical pairs are confirmed
to fit the rival; every four-pair schedule window remains identifiable under all
four query rotations in focused tests and the 1,200-rotation census.

**Failure mode/limit.** Only the declared first-seen rival is exhaustively
checked; finite rivals do not establish universal induction.

## D6 — Validate a strict, canonical-compatible sampler manifold

**Choice.** `self_check` and `strict_canonical_like` require a rectangular ARC
grid, one of the six supported shapes, the profile's expected number of colors,
per-color counts in `1..4`, and a one-row result no wider than the input.
Canonical tied counts are accepted.

**Alternatives rejected.** Keeping the baseline's distinct-count validator would
reject a canonical pair. A fully total-rule validator would make profile claims
unmeasurable and accept unrelated distributions.

**Probe/evidence.** All five labeled canonical inputs pass; malformed, wrong
shape, wrong count, and out-of-domain examples are tested. Final self-check and
strict-profile stages pass.

**Failure mode/limit.** Some lawful total-rule inputs are intentionally rejected
because this is a sampler-domain validator, not the Racket rule's full domain.

## D7 — Declare and exhaust the widened finite output codomain

**Choice.** Set `EXPECTED_OUTPUT_CODOMAIN = 552`. Per palette, supported
assignments contribute 18 three-color tied bars, 24 three-color distinct bars,
72 four-color tied bars, and 24 four-color distinct bars: `4 × 138 = 552`.
The focused test enumerates the exact union rather than estimating it by random
sampling.

**Alternatives rejected.** Keeping the first repair's 24 fixed layout/palette
labels preserved a direct profile-lookup shortcut. Suppressing finite-codomain
lint without exact enumeration would be unsupported; unconstrained counts would
weaken the strict sampler contract and schedule guarantees.

**Probe/evidence.** The intermediate battery retained at
`checks/after-intermediate-codomain-bands/` exposed the original missing
codomain declaration. Final-review anti-lookup tests then forced the widening;
the exact-support test passes and final lint/defect lint are green.

**Failure mode/limit.** The curriculum remains finite. Changing palettes,
frequency signatures, or count bounds requires updating and re-exhausting the
declaration.

## D8 — Make difficulty streams distinct without changing semantics

**Choice.** Difficulty selects a separate deterministic placement RNG stream;
shape/count teaching cadence remains identical across bands.

**Alternatives rejected.** Making hard examples semantically underdetermined or
changing witness frequency by band would complicate lesson guarantees. Leaving
bands byte-identical triggered a valid dead-band warning.

**Probe/evidence.** A regression asserts four distinct deterministic grids for
the same seed/index across `None`, easy, medium, and hard. Final defect lint
passes; each band has 400 unique census inputs.

**Failure mode/limit.** Difficulty means spatial variation, not monotone logical
complexity; this is stated rather than implied otherwise.

## D9 — Use three demonstrations and verify all query rotations

**Choice.** Keep `EXAMPLES_NEEDED = 3`; arrange each four-pair window so removing
any one query still leaves a tie witness among the demonstrations, while every
pair already contains the component witness.

**Alternatives rejected.** Two demonstrations cannot guarantee both distinctions
under arbitrary holdout; adding more examples is unnecessary for the declared
finite rivals.

**Probe/evidence.** Exhaustive local windows over all cyclic starts and bands
pass. The external census materialized 300 lessons, 1,200 pairs, and 1,200
rotations with zero ambiguity or errors.

**Failure mode/limit.** The census and local tests cover declared rivals and the
six-position schedule, not all conceivable hypotheses.

## D10 — Preserve failed evidence and solve records

The before battery, the two-warning intermediate battery, both anti-lookup RED
runs, resumed final battery journal, portable task tests, blind solve, and
exposed solve records were all retained. When v3.1.0 changed generator bytes,
the v3.0.0 exposed episode was moved under
`checks/prior-solve/3f6deb4676f7298999e53e9b7e5e154cab74707cf49a7727fced12ca1ba375da/`
and a fresh visible-only solve was prepared. Both exposed solves honestly mark
earlier rule exposure and no reference consultation during their solve lanes.

## D11 — Decouple frequency assignments from observable profiles

**Finding.** In v3.0.0 each layout had one fixed count tuple and counts were
zipped to colors in numeric order. Shape plus palette therefore determined the
entire output bar without inspecting how many cells of each color were present.

**Choice.** Keep `layout_profile` and `palette_profile` exact and observable, but
sample a lawful tied/distinct frequency signature and a permutation assigning
that signature to colors using an independent keyed RNG. Preserve the adjacency
and reverse-first-seen witnesses during placement.

**Alternatives rejected.** Merely documenting the 24-case lookup would leave the
curriculum semantically weak. Hiding shape/palette controls would fix the symptom
by breaking the override contract. Randomizing only positions would not change
the output lookup.

**Probe/evidence.** Two regressions failed against v3.0.0 (`2 failed, 132
passed`) and pass in v3.1.0 (`134 passed`).
`checks/anti-lookup-witness.json` holds two cases with the same shape, palette,
tie mode, and total painted-cell count but different correct outputs. The final
battery and 1,200-rotation census remain green.

**Failure mode/limit.** This rules out the direct observable-profile lookup and
fixed numeric-rank assignment, not every possible finite-support memorizer.
