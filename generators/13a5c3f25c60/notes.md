# Current notes: 13a5c3f25c60

## Intended rule

The top-left corner is a source-color legend and the top-right corner is a
distinct target-color legend. Preserve both corners. Recolor every other source-
colored cell to target; preserve all other cells. The selected Racket authority
is unchanged and pinned by `RULE_HASH = 2ba5a8d2d710`.

## Current sampler decisions

Version `2.0.0` exposes four exact observable controls only:
`grid_h=7..9`, `grid_w=8..11`, `source_cells=2..8`, and `distractors=0..6`.
Unknown, mistyped, and out-of-range controls fail loudly. Every Cartesian
combination is constructive.

Ordinary examples always contain at least one non-corner source cell on row 0
and one below row 0. This refutes both `below_top_row_only` and `top_row_only` in
an individual pair. The source legend corner refutes `recolor_source_corner`.
Ordinary target color is an interior active-palette rank, and a row-0 distractor
prevents position alone from identifying source cells. Explicit
`distractors=0` remains a supported diagnostic override but is not selected by
default.

Canonical dimensions/palette sizes are weighted through four internal profiles;
the public dimensions remain exact scalars and every bound is available in every
difficulty band. Difficulty changes only source-count preference.

## Evidence

The prior unresolved audit in `evidence/review_index.json`, bound to baseline
SHA-256 `3466b8d49cea0c02ec043d8793d00585d07dd28db3edeac85af3a807207fec48`,
was used as a lead. The local before battery independently reproduced its
row-partition and override-contract concerns.

Final generator SHA-256:
`5091d619574aac517969bf4df8caf253c90749d60c52e5f895812951ed456b8f`.
Final task-test SHA-256:
`5571531d0238edab892afab7aa559acb98e8c4c4bf98e9c6aee6b12908933170`.
The final battery is 12/12 green; 56 focused tests pass. A 300-lesson census
(three demos plus one query) materialized 1,200 unique pairs and found no
production or query-rotation ambiguity against declared rivals.

## Known limits and open findings

The sampler intentionally does not train invalid historical textures or canvases
outside 7–9 by 8–11. Its declared rival set is finite, and the random census does
not exhaust all seeds. Selected authority synchronization is green; an archival
bank variant remains divergent as pre-existing nonblocking evidence. No open
finding remains for this repair.
## Current reviewer considerations

Source SHA-256: `5091d619574aac517969bf4df8caf253c90749d60c52e5f895812951ed456b8f`.

# Decision ledger — 13a5c3f25c60

Finding IDs refer to `REVIEW.md`.

## D1 / R1 — Keep the selected Racket authority unchanged

- **Original rationale:** the selected authority already matched every canonical
  pair and precisely excludes only the two corner legend cells from recoloring.
- **Decision:** pin `RULE_HASH = "2ba5a8d2d710"` and repair the input/lesson
  manifold rather than changing semantics.
- **Alternatives considered:** reinterpret the entire top row as legend; alter
  the rule to preserve all row-0 cells; edit canonical outputs. Each would make
  the prior shortcut authoritative instead of teaching the selected rule.
- **Probe:** canonical independent mirror, rule-smoke, authority-sync, and the
  post-repair visible-only solve.
- **Limit:** the Racket function still accepts grids outside the sampler's
  intentionally bounded teaching manifold.

## D2 / R2 — Reduce the public override surface to four exact pixel properties

- **Original rationale:** version 1.2.1 attempted broad diversity through ten
  controls, including palette aliases, fixed metadata labels, and invalid
  teaching textures.
- **Decision:** expose only `grid_h`, `grid_w`, `source_cells`, and
  `distractors`; implement `observe_overrides` for all four.
- **Alternatives considered:** implement every historical axis literally;
  preserve aliases for compatibility; declare large incompatibility tables.
  Those choices would retain a contract larger than the rule or evidence needs.
- **Probe:** every boundary and representative joint extreme in every band,
  plus the generic override stage.
- **Limit:** callers using old private controls now receive an explicit unknown-
  axis error and must migrate.

## D3 / R2 — Use canonical-scale dimensions with weighted, not clipped, support

- **Original rationale:** the baseline advertised heights 3–16 and widths 4–18,
  while defaults and canonical examples occupied a much smaller region.
- **Decision:** lawful heights are 7–9 and widths 8–11. A four-profile schedule
  weights the exact canonical dimensions, but the full advertised range remains
  selectable in every band.
- **Alternatives considered:** expose a categorical profile axis; keep broad
  independent ranges; hard-code one canonical size. Independent exact scalar
  dimensions are easier to inspect and still allow all canonical profiles.
- **Probe:** profile-floor gate, 20-draw band tests, and exact dimension
  overrides.
- **Limit:** extrapolation to larger or smaller canvases is not trained or
  claimed.

## D4 / R1 — Put both row-partition witnesses in every ordinary example

- **Original rationale:** the prior sampler shuffled all non-corner cells, so a
  row-0 source was possible but not guaranteed in a complete lesson.
- **Decision:** reserve one row-0 non-corner source and one below-row source
  before placing any additional source cells.
- **Alternatives considered:** rely on random coverage across three demos;
  require only one witness somewhere in a scheduled lesson; increase demo count.
  Per-example construction is simpler and survives arbitrary query rotation.
- **Probe:** 64 draws per band, all cyclic query positions in focused tests, and
  the 1,200-rotation census.
- **Limit:** this intentionally overrepresents examples where both row regions
  contain source cells; it optimizes teaching clarity over matching an unknown
  natural frequency.

## D5 / R3 — Prevent color rank and row position from replacing the intended cue

- **Original rationale:** the first witness repair selected source/target colors
  freely, which sometimes made target the smallest or largest active color.
- **Decision:** choose three ordered nonzero colors and assign target to the
  middle rank; source and the primary distractor take the extremes. Ordinary
  samples contain at least one distractor, including one on row 0.
- **Alternatives considered:** randomize all color roles and rely on a large
  multi-demo schedule; add only a numeric-rank rival; forbid row-0 distractors.
  Construction gives cheaper, local evidence and avoids position/color
  confounding.
- **Probe:** a red regression first failed four band cases, then 56 focused tests
  and the strict semantic gate passed.
- **Limit:** explicit `distractors=0` cannot demonstrate an interior active rank;
  it is retained as a diagnostic exact override but excluded from ordinary
  production draws.

## D6 / R2 — Reject malformed scalar inputs at the generator boundary

- **Original rationale:** `gen_ctx` could accept or coerce values that made the
  public contract ambiguous, including booleans and unknown keys.
- **Decision:** require literal integer `seed`, nonnegative literal integer
  `sample_index`, a known difficulty, known axes, and literal integer override
  values in range.
- **Alternatives considered:** rely entirely on downstream helper validation;
  silently ignore unknown keys; coerce numeric strings/floats. Loud rejection is
  safer for reproducibility and provenance.
- **Probe:** targeted test matrix and the final defect-lint/override stages.
- **Limit:** error classes differ slightly between top-level seed validation
  (`TypeError`) and override validation (`ValueError`); both are intentional
  hard failures rather than coercions.

## D7 / R4 — Declare executable witnesses and rivals

- **Original rationale:** the baseline had no task-linked semantic contract, so
  feature presence could be mistaken for evidence against an alternative rule.
- **Decision:** declare `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`,
  `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and a pure
  `lesson_identifiable` hook.
- **Alternatives considered:** prose-only notes; generic battery rivals only;
  a task-specific resampling callback. Executable local functions are easier to
  replay and inspect.
- **Probe:** semantic gate and 300-lesson source-bound census with every query
  rotation required.
- **Limit:** the rival set is finite; passing it is evidence against named
  shortcuts, not a proof of globally unique induction.

## D8 — Use three demonstrations and one query without ordered dependence

- **Original rationale:** three demonstrations are the packet's default and
  provide ample palette/layout diversity.
- **Decision:** set `EXAMPLES_NEEDED = 3`, but make every individual ordinary
  pair carry all required witnesses so no particular demo position is special.
- **Alternatives considered:** one demonstration; a fixed witness slot; a
  declared schedule period. One demo would likely suffice for the named rivals,
  but three preserves diversity; a fixed slot would create the ordering failure
  observed in audit target `97e1d2aa0bc3`.
- **Probe:** 300 production lessons and all 1,200 held-out rotations.
- **Limit:** the census samples seeds and starts; it does not exhaust the
  infinite seed space.

## D9 — Make difficulty a soft count preference, not a grammar switch

- **Original rationale:** the baseline changed dimensions, source counts, and
  distractor counts by band, causing advertised boundaries to disappear in some
  bands.
- **Decision:** all bands share one grammar and exact override support. Difficulty
  changes only weighted source-count preferences.
- **Alternatives considered:** separate per-band ranges; larger canvases at hard;
  no difficulty effect. A soft preference preserves exact-control truth and
  gives a modest visible progression.
- **Probe:** exact extrema in `None`, easy, medium, and hard; profile floor in all
  named bands.
- **Limit:** difficulty is distributional rather than a guaranteed complexity
  interval.

## D10 — Preserve invalid historical textures only as evidence, not production

- **Original rationale:** the old generator exposed `missing_legend`,
  `source_equals_target`, and `no_source_in_body` as textures, likely to increase
  edge-case diversity.
- **Decision:** remove them from the lawful generator contract. Retain the prior
  audit manifest and before-check evidence rather than generating mislabeled or
  transformation-free training pairs.
- **Alternatives considered:** negative examples with special labels; validator-
  only fixtures; explicit incompatible combinations. This pipeline exports
  ordinary labeled transformations, so invalid/identity degenerates belong in
  tests, not its positive sampler.
- **Probe:** strict self-check fixtures and final grammar/distribution stages.
- **Limit:** this repair does not create a separate negative-example curriculum.
