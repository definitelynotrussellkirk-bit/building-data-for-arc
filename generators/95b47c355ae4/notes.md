# Current generator notes: 95b47c355ae4

## Intended rule

Every input color-6 singleton is erased and repainted one row down and one
column right. Color-5 cells are static decoration. The selected Racket authority
was not changed; `RULE_HASH = 76edf9516933` pins it.

## Current input contract

- Canvas: 8–10 rows by 8–10 columns.
- Moving cells: exactly 3–7 color-6 cells, 4-neighbor isolated, with an empty
  in-bounds `(r+1,c+1)` destination.
- Decoration: exactly 3–12 color-5 cells, disjoint from every source and target.
- Exact observable controls: `grid_h`, `grid_w`, `n_6_cells`, `n_5_cells`.
- Unknown, retired, non-integer, or out-of-range controls fail loudly.

Default dimensions cycle through the three canonical square profiles. Counts
cycle through canonical and broader values; keyed randomness varies source
locations and gray topology. Every generated scene includes a left-edge source
and color-6 sources on both row parities and both column parities. This makes
wrong direction/clipping and parity-filtered shortcuts directly observable.

## Reversed decisions

The legacy generator exposed nine axes plus diagnostic textures, but most were
aliases, inert, silently clamped, or incompatible. They were removed rather
than preserved as misleading compatibility surface.

The first repair used one parity lattice to guarantee isolation. A final
shortcut review showed that `move_even_columns_only` and a one-row-parity rule
would fit all generated scenes. That placement was replaced with constrained
scattered sampling, and two parity witnesses/rivals plus a regression test were
added. Evidence: `checks/parity-red/`, `checks/parity-green/`, and the final
semantic report.

## Verification and limits

Final generator SHA-256:
`c0e48a0255cb2567a075d8cf96cd8d0cf29b456f941e28ec86434d7f91fd084b`.
The final 12-stage battery and 43 task-local tests pass. A 300-lesson census
with three demonstrations and one query checked all 1,200 query rotations and
found no ambiguity among the six declared competitors. This is finite
rival-based evidence, not a proof against every possible learned rule. The
sampler deliberately excludes edge-clipped moves, touching source cells, and
blocked destinations; those are outside the documented lawful input domain.
## Current reviewer considerations

Source SHA-256: `c0e48a0255cb2567a075d8cf96cd8d0cf29b456f941e28ec86434d7f91fd084b`.

# Decisions for 95b47c355ae4

## D1 — Preserve the selected transformation authority

**Prior state.** The generator had no `RULE_HASH`; the canonical Racket program
already matched all canonical labels. The original rationale was not recorded.

**Decision.** Keep the Racket source unchanged and pin its normalized hash
`76edf9516933`. Add a Python mirror only for tests and semantic diagnostics.

**Rejected alternatives.** Rewriting the Racket program would increase authority
scope without fixing the data defects. Generating labels in Python would create
a second authority.

**Evidence/failure mode.** Rule smoke, Racket lint, and authority sync are green
in the final battery. A future selected-rule change must update the pin and all
source-bound evidence atomically.

## D2 — Replace nine misleading axes with four exact observable controls

**Prior choice.** `palette_kind`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture` were advertised alongside dimensions
and source count. Their original rationale is unknown; several were singleton,
unused, aliases, or invalid-data modes.

**Decision.** Expose only `grid_h`, `grid_w`, `n_6_cells`, and `n_5_cells`.
Every accepted value must appear exactly in returned pixels and be recoverable
by `observe_overrides`. Retired and unknown keys fail loudly.

**Rejected alternatives.** Preserving aliases for compatibility would keep silent
misconfiguration possible. Making all old fields real would add variation that
does not teach another branch of the rule.

**Evidence.** Baseline: 4,989 findings over 64,260 override draws, including
3,780 mismatches and 1,080 generation errors. Final: 0 findings/warnings over
15,570 draws across 173 cases and all three bands.

## D3 — Define the actual lawful input grammar

**Decision.** Use 8–10 rows/columns, 3–7 isolated color-6 sources, and 3–12
color-5 cells. Every source must have an empty, in-bounds down-right destination;
all cells are literal integers in `{0,5,6}`.

**Why.** These bounds contain all five canonical inputs while leaving useful
count and topology variation. The rule is clearest when collisions and clipping
are not implicit extra branches.

**Rejected alternatives.** The baseline minimum of four sources rejected a
canonical example with three. Allowing edge clipping or blocked targets would
introduce semantics not demonstrated by the canonical task. Diagnostic invalid
textures belong in tests, not ordinary training data.

**Limit.** This is a deliberate clean-translation extension, not a claim about
collision resolution or touching magenta objects.

## D4 — Anchor every difficulty band to canonical profiles

**Decision.** Cycle default square dimensions through 8, 9, and 10 in every
band; cycle source and gray counts through canonical values plus modest broader
values. Explicit dimensions remain independent, so rectangular joint overrides
are still legal.

**Why.** The old band-specific ranges made easy/hard controls incompatible and
left exact-profile support accidental. Deterministic recurrence guarantees all
bands retain canonical scale while keyed layout randomness provides diversity.

**Evidence.** Final profile floor accepts 5/5 canonical inputs and records
60/60 exact-profile plus 60/60 envelope hits. Distribution tests observe all
three canonical sizes and required counts in each band.

## D5 — Use constrained scattered sources, not a parity lattice

**First repair choice.** Sources were drawn from one checkerboard sublattice.
This cheaply guaranteed isolation and source/target disjointness.

**Reversal.** A final self-review added a test for coordinate support and watched
it fail: every scene used one row parity and even columns. A model could learn
`move_even_columns_only` or a same-row-parity shortcut.

**Final decision.** Use constrained scattered placement with one left-edge
source plus a forced odd-column/opposite-row-parity source, then fill under
4-neighbor and source/target-disjointness constraints. Every scene therefore
contains both row and column parities.

**Evidence.** `checks/parity-red/` records the expected failure; 43/43 final tests
pass. New parity witnesses fire 600/600 times and their two rivals disagree in
all 60 sampled authoritative checks each.

## D6 — Vary gray topology while keeping gray semantically static

**Decision.** Keep gray count exact but mix scattered, one-cluster, and
multi-cluster layouts using keyed randomness. Gray cells never overlap a source
or its destination.

**Why.** A fixed decoration template would invite location-specific shortcuts;
fully arbitrary noise could obscure the only moving color. The selected modes
vary component topology while preserving the simple static-role contrast.

**Evidence.** Task tests require at least five observed gray component profiles
per band. Diversity and grammar stages pass.

## D7 — Turn plausible shortcuts into executable contracts

**Decision.** Declare identity, copy-without-erasing, down-left, move-all-nonzero,
even-columns-only, and even-rows-only competitors. Bind five semantic witnesses
to the rivals they are intended to refute.

**Why.** Correct individual labels do not guarantee a teachable lesson. The
baseline had no way to say which wrong rule survived a demonstration set.

**Rejected alternative.** A prose list or witness frequency alone cannot prove
a wrong program changes authoritative output. Exhaustive program synthesis is
not affordable or complete.

**Evidence/limit.** Final smoke gate: 12/12 lessons and 48/48 rotations identify
all declared rivals. The larger census checks 300 lessons and all 1,200 rotations
with zero ambiguity. Undeclared hypotheses remain possible.

## D8 — Build source-bound regressions before trusting broad gates

**Decision.** Add task-local tests first and retain both red and green evidence.
The initial suite failed 33 tests on the baseline. A later parity regression
failed three band cases on the first repair before the source was changed.

**Why.** The shared battery is broad, but exact task semantics, retired controls,
and new shortcut reproductions need a portable local contract.

**Evidence.** Final isolated task suite is 43/43. Full final battery is 12/12.
The final visible solve is regenerated from and hash-bound to the same generator
bytes.

## D9 — Curriculum composition annotation

No optional ARC-DESIGN composition axis is asserted. Static gray decoration and
translation of multiple same-role sources do not clearly establish cue-gated
subrules or sequential composition. Leaving this unknown is more accurate than
inflating coverage.
