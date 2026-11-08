# Current account: 67a09b7f6b66

## Rule and authority

Version `2.1.0`; canonical `RULE_HASH=100ba25d6ec9`.
Read the ordered legend at row 0, columns 1–3. For each of three color-8-walled
chambers, count color-1 dots and fill the chamber interior with
`legend[count-1]`. Color 8 may also be a legend color; roles are positional.
No Racket/canonical rule change was made in review `review-94d3f68e4d451322`.

## Current input contract

Public exact axes are:

- `ch_h`: 5..9;
- `ch_w`: 3..5;
- `palette_kind`: `wall_excluded|wall_shared`;
- `count_order`: all six permutations of `123`.

Every joint override is lawful in every band; unknown or ill-typed controls are
rejected. `observe_overrides` recovers all values from the grid. Default
12-slot dimension schedules are half canonical `6x3` anchors and half full-domain
coverage. Palette and count-order schedules use periods 5 and 6 respectively.

The validator is structural and metadata cannot waive it. Each chamber must
retain exactly one connected zero region and every dot must touch it, matching
the selected Racket authority's connected-region behavior.

## Reversed baseline decisions

The imported v1.2.1 contract exposed singleton/inert axes and a texture domain
containing `no_dots`, `no_legend`, and `no_walls`. Those were removed because
ordinary generation must remain lawful and observable. Difficulty-specific
clamping was removed because it contradicted global exact domains. Legend color
8 is now accepted because two canonical inputs use it. An initial v2 repair with
15% canonical-profile support was replaced by the 50%-anchor schedule after the
pinned profile-floor warning.

## Shortcut curriculum

Canonical pairs admit two named rivals:

- `position_only`: fill chambers by left/middle/right legend position;
- `occupied_rows`: use number of dot-containing rows rather than dots.

Generation cycles noncanonical count orders and, on even sample indices, puts
the two-dot chamber's pair on one row. Exact Racket-checked reproducers are in
`counterexamples/position-only-witness-v2/` and
`counterexamples/occupied-rows-witness-v2/`. Three-demo lessons require a
wall-shared palette and reject both rivals. Final evidence: 12/12 smoke lessons,
0/48 required rotation ambiguities; 300/300 larger-census lessons and 0/1,200
rotation ambiguities.

## Known limits and future checks

This remains the canonical three-chamber/counts-1..3 task. The finite rival set
is not a uniqueness proof. Preserve all six count orders, same-row witnesses,
wall-shared palettes, one-zero-region safety, and at least one exact canonical
profile per band after schedule changes. `GenCtx` lacks a public scheduled-axis
recorder, so `_scheduled_axis` currently isolates private `ctx._record` use.
## Current reviewer considerations

Source SHA-256: `df01780544b9e505813229e1072ec11689ac9798c49213b1d29a00c4fdaf7dd2`.

# Design decisions for `67a09b7f6b66`

## Authority and intended rule

The canonical authority is unchanged and pinned as `RULE_HASH=100ba25d6ec9`.
The input has an ordered three-color legend at row 0, columns 1–3, and three
color-8-walled chambers. A chamber containing `n` color-1 dots is filled with
legend entry `n` for `n in {1,2,3}`. Color 8 is contextual: it may be both a
wall color and one legend entry.

I did not alter canonical data or Racket source. A Python mirror exists only for
validation, executable rival checks, and focused tests; Racket application is
retained for authority binding.

## Public axes

### `ch_h: 5..9`

This is the number of chamber-interior rows; total height is `ch_h + 3`.
The prior generator declared this range but silently narrowed it by difficulty,
causing legal exact overrides to fail. The final generator accepts all five
values in every band and makes the realized value observable from the grid.

### `ch_w: 3..5`

This is each chamber's interior width; total width is `3*ch_w + 4`.
All three values are accepted in every band. Wider cases prevent a solver from
hard-coding the canonical 13-column layout without adding irrelevant shapes.

### `palette_kind: wall_excluded | wall_shared`

`wall_excluded` samples three legend colors excluding 8.
`wall_shared` samples two non-wall colors plus 8 and shuffles their order. The
old `default/warm/cool/varied` labels were rejected because they were either
inert or did not describe a semantic role. The five-slot default schedule uses
`wall_shared` in three slots, de-correlated from the six count orders; the final
600-draw semantic census measured 347/600 wall-shared cases.

### `count_order: 123 | 132 | 213 | 231 | 312 | 321`

This is the left-to-right permutation of chamber dot counts. It is the essential
anti-shortcut axis: the canonical data always uses `123`, so a positional fill
rule otherwise fits every demonstration. The default schedule cycles all six
orders, and exact overrides cover every combination with the other axes.

No incompatible override combinations are declared because all 5 × 3 × 2 × 6
= 180 joint settings are lawful in every difficulty band. Focused tests execute
all 180 settings per band; the shared override audit executes 9,720 draws across
108 planned cases and reports zero findings.

## Default dimension schedules

Each difficulty has a deterministic 12-slot `(ch_h,ch_w)` schedule. Six slots
are the canonical `6x3` chamber profile; the other six jointly cover every
advertised height and width. This replaced the first repair's sparse 15%
canonical-profile rate. The final pinned profile-floor draw observed 31/60 exact
canonical profiles, and the broader semantic census observed 297/600 strict
canonical profiles (49.5%), while all bands retained noncanonical sizes.

Difficulty remains a curriculum label rather than a restriction on exact
controls. That avoids the baseline contradiction where an axis was advertised
globally but rejected in some bands.

## Dot geometry and Racket-lawfulness

The selected Racket program reasons over connected zero regions. Unconstrained
random dots can isolate a corner zero cell and make Racket fill it separately,
even though a rectangular Python abstraction would still see one chamber.
Therefore each chamber now rejection-samples dots until:

1. the remaining zero cells form exactly one 4-connected component; and
2. every dot is orthogonally adjacent to that component.

This is a necessary authority-domain constraint, not cosmetic regularization.
It preserves all counts, sizes, palettes, and count orders.

For the two-dot chamber, even sample indices deliberately place both dots in one
row. This distinguishes true dot count from the canonical-fitting
`occupied_rows` rival. Other cases remain random subject to authority safety, so
the witness is common rather than exclusive; the semantic census measured it in
421/600 draws.

## Validation and provenance

`self_check` now parses the full ordinary grammar and never trusts metadata to
waive it. It checks rectangular integer ARC grids, dimensions, legend placement,
all walls, chamber colors, one connected zero region per chamber, dot adjacency,
and count multiset `{1,2,3}`. `strict_canonical_like` adds only the canonical
`ch_h=6,ch_w=3` profile restriction.

`observe_overrides` reconstructs all four public axes from a lawful grid. Unknown
keys, non-exact types such as booleans/floats, invalid difficulty labels, and
out-of-domain values raise rather than silently clamp.

The only shared-runtime compromise is `_scheduled_axis`: `GenCtx` has no public
method to record a deterministic scheduled default while retaining exact override
provenance, so the helper isolates one call to private `ctx._record`. F1 in
`FEEDBACK_TO_CODEX.md` proposes the shared API needed to remove that dependency.

## Lesson policy

`EXAMPLES_NEEDED=3`. Production assembly supplies three ordered demonstrations
and one query. A lawful lesson must:

- contain correctly Racket-mirrored labels;
- include a wall-shared palette example;
- refute `position_only`; and
- refute `occupied_rows`.

The final battery ran the 12-lesson smoke test with all 48 single-query rotations
required and found zero ambiguities. The larger source-bound census materialized
300 production lessons and checked all 1,200 held-out rotations, again with zero
declared-rival ambiguities and 1,200 unique inputs. The policy therefore supports
arbitrary query placement among the four materialized pairs, not only the
production last-query order.

This is intentionally finite: it certifies the named plausible rivals and hook,
not every computable rule. Adding a newly discovered plausible canonical-fitting
rival should require an executable rival, a generated witness, and a regression
test rather than an unsupported prose claim.

## Rejected alternatives

- **Keep `no_dots`, `no_legend`, or `no_walls` as textures:** rejected because
  they are malformed negatives, not lawful task inputs.
- **Keep `default/warm/cool/varied` palette labels:** rejected because their
  observable semantic distinction was absent; replaced by the exact contextual
  role of color 8.
- **Retain singleton `palette_size`, `n_distinct_colors`, `density`, or
  `position_bias` axes:** rejected because they cannot demonstrate override
  effects and inflate the contract without adding coverage.
- **Clamp dimensions by difficulty:** rejected because exact public controls must
  remain truthful in every band.
- **Use arbitrary dot positions:** rejected after an exact Racket mismatch showed
  disconnected zero pockets.
- **Teach only noncanonical count order:** insufficient; it kills the positional
  rival but not `occupied_rows`.
- **Keep the first 15%-canonical schedule:** rejected by the pinned profile-floor
  warning; replaced by 50% nominal canonical anchors.
- **Change the Racket authority:** rejected because the canonical program was
  internally consistent; the generator needed to respect its connected-region
  semantics.

## Known limits

The domain remains three chambers, counts 1–3, a top legend, and color-8 walls;
that is the canonical task rather than an attempt to generalize to arbitrary
legends or chamber counts. The generator is not catalog-approved by this review,
and the return does not admit training data. Declared-rival and finite-census
successes do not establish universal identifiability.

## Current lesson-boundary repair

The retained metadata audit binds source `0b7900f0c0fac180b0c8d4fca84e384a5b40585330b9b0b4cd93ab45a9d65d6d`,
not the incoming `81fcce3e0f52d435966d1cff8bf70298d3e495132e56a41b762274b299b03b73`.
A fresh incoming-source probe rejected all three retained malformed inputs even
with their texture metadata. The old texture control is absent. No duplicate
texture patch was applied; the frozen audit index was preserved for owner disposition.

Two current defects were reproduced before editing. First, `lesson_identifiable`
accepted noninteger labels because Python equates `False` with `0` and integral
floats with integers. Both demonstrations and queries could pass this check.
Second, `_parse_grid` accepted tuple inputs while the mirror either returned a
tuple instead of its promised list grid or failed when assigning into tuple rows.
The repair validates output dimensions and exact integer ARC colors before label
comparison, explicitly retains list-of-lists output labels, and materializes list
rows when filling either accepted input container. It changes no generation RNG,
axis, schedule, canonical data, Racket program, or rule hash. Version remains
`2.1.0` to preserve every existing seed/index draw.

Six new regression cases failed against the incoming source. Final isolated
`task_tests --phase after` passed 57 cases (including all prior exact-domain,
canonical, metadata, connected-region and cyclic lesson tests). Actual pinned
Racket execution matched all five canonical pairs and twelve generated cases
covering all count orders, both palettes, every height/width and all bands:
17/17 labels matched, with the executed rule pinned to `100ba25d6ec9`.
Reproducer: `workspace/lesson_hook_probe.py`; retained machine evidence:
`WORK/checks/67a09b7f6b66/lesson-hook-before.json`, `lesson-hook-after.json`,
`regressions-before.log`, `task-tests-final-v2/result.json`,
`authority-racket.json`, and `authority-parity-summary.json`.
These are focused checks, not a new catalog approval or a full-battery claim.
An initial authority launcher used a relative interpreter path after the wrapper
changed cwd; the failed receipt is retained and the corrected absolute-path run passed.

## Native parametric admission review-c83611f00afef4d0 (2026-10-24)

The production generator and canonical authority remain byte-identical to the
incoming packet. The task-local native family adds one episode-fixed parameter,
`legend_mapping`, with exact canonical default `absolute_count` and composed
alternative `anchor_cycle`. The canonical Racket program is preserved at SHA-256
`100ba25d6ec97cde77221669057e2d781d0c652551305a44fd03cd43e86acebf`;
the alternative program is
`cd0b28e03ef2a89e952ec799bd6aac9ace1fb8fbf8b0c6a52628263928063cbc`.

`anchor_cycle` marks exactly one chamber at its upper-left interior cell. Step A
locates that chamber and counts all of its dots, producing anchor count `k`.
Step B cannot choose its colors before `k` is known: each chamber count `n` maps
to legend slot `1 + ((n-k) mod 3)`. A source-bound protected-Racket witness uses
a retained `k=2` input and shows that forcing the wrong intermediate `k=1`
changes the final output.

The adapter supports 2–6 demonstrations, stable 1–4 query prefixes, and four
stored distinct queries. Both settings share inputs. The fourth query is an
actual 30×30 instance with unequal chamber widths and substantive filled area.
The finite teaching audit tested position-only, occupied-row, and fixed-anchor
competitors as relevant to each setting; none survived all visible demonstrations
while changing a query across three seeds. It executed 124 protected-Racket
labels and 128 deterministic prefix/count-boundary checks. Native qualification
passed both settings on seeds 0 and 17 with four queries, 32 protected-Racket
evaluations, and a clean public projection. The full changed-target suite passed
82/82.

Retained evidence is under
`workspace/parametric/evidence/`, `WORK/checks/67a09b7f6b66/qualification/`,
and `WORK/checks/67a09b7f6b66/causal/`. This is reviewer-ready, not accepted:
owner integration, exact-live-byte qualification, acceptance replay, and any
training admission remain pending. The finite rival audit is not a universal
uniqueness proof.
