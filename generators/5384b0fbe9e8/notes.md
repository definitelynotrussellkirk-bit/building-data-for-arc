# Working notes: 5384b0fbe9e8

## 2026-09-28 review: lesson-level shortcut identifiability

The canonical five pairs each contain at most one mark per row, at most one
mark per column, and one occurrence of every mark color. Therefore three wrong
rules reproduce every canonical answer: mirror only the first mark in each row,
only the first mark in each column, or only the first occurrence of each color.

A deterministic census of 600 draws per difficulty found that these shortcuts
could survive contiguous three-demo windows in the v2.0 distribution. The
largest measured gap was the row-limited shortcut on easy draws: 73 of 598
windows contained no counterexample.

Version 2.1 retains the four exact canonical morphologies on a 3-of-10 schedule.
Every generalized draw now includes a repeated row, repeated column, and
repeated color, and no three consecutive sample indices can all be canonical
anchors. The generator declares the three rivals, their witnesses, the schedule,
and a lesson-identifiability hook so the shared semantic gate verifies the
curriculum rather than relying on morphology alone.

The authoritative Racket rule is unchanged. Whole-grid-center reflection and
reflection around the centered divider remain observationally equivalent on the
lawful grammar; no generated example can separate them without changing the
task domain.
## Current reviewer considerations

Source SHA-256: `281139229aacc593a802d9b1b361316ee01d786a81d03f9097761ebe544d63a3`.

# Decisions: 5384b0fbe9e8

## Objective and constraints

The goal was to improve training value without changing the task grammar:
centered full-height color-5 divider, equal-width panels, populated left panel,
empty right panel, and color-preserving reflection into the right panel. Success
required preserving canonical support, exact overrides, Racket authority, and
all inherited checks while making three-example lessons identify the intended
operation rather than a canonical-only shortcut.

## D1: Preserve canonical anchors, but schedule them

**Input choice.** Keep the existing 30% canonical-profile mass, represented as
three fixed anchor positions in every ten consecutive sample indices.

**Original rationale.** Prior retained evidence deliberately added a canonical
mixture because purely broad sampling could pass diversity checks while rarely
resembling the five demonstrations. The imported version measured substantial
strict canonical-like support and had a 5% minimum profile floor.

**Alternatives considered.**

- Remove canonical anchors: strongest anti-shortcut coverage, but loses the
  demonstrated scale and morphology anchor.
- Keep independent 30% draws: preserves marginal support, but permits three
  canonical examples in the same lesson.
- Rejection-sample complete lessons: works at episode construction time, but the
  generator is called pair-by-pair and the task-local contract should remain
  useful to every caller.

**Probe.** The v2.0 census found shortcut-compatible three-demo windows even
though most individual generalized draws were good. The scheduled version has
zero such windows in 598 starts per band and retains 180/600 canonical anchors
for sequential indices.

**Failure modes and limits.** A caller can choose arbitrary nonconsecutive
indices, so the schedule alone is not a complete guarantee. The separate
`lesson_identifiable` hook checks the actual demos and query.

## D2: Construct row and column collisions instead of hoping to sample them

**Input choice.** In every generalized draw, place a far-edge mark and an
interior mark in the same row, plus another mark in the same interior column on
a different row. Keep a divider-adjacent mark on another row.

**Original rationale.** Version 2 already required far- and near-divider marks,
multiple rows, several colors, and an empty right panel. That design strongly
covered reflection geometry, but row and column multiplicities were incidental.

**Alternatives considered.**

- Continue uniform position sampling and raise sample counts: cheaper source
  change, but leaves a nonzero probability of weak lessons.
- Rejection-sample until both collisions occur: semantically valid, but adds
  variable runtime and can complicate exact reproducibility.
- Construct the witnesses directly: constant-time, transparent, and exactly
  testable. This was selected.

**Probe.** Baseline easy draws refuted the row-limited rival only 313/600 times.
The revised generalized branch refutes it 420/420 times; the same is true for
the column-limited rival.

**Failure modes and limits.** Constructive positions introduce correlations.
The remaining marks are still sampled over the lawful panel, and diversity and
profile gates remained green. Two reserved opposite-extreme cells stay empty to
retain a deterministic disagreement with straight/non-reflecting panel copy.

## D3: Guarantee a repeated color through mark count

**Input choice.** Generalized draws always use more marks than palette colors.
Palette support remains 3..5 colors; the existing difficulty-skewed mark-count
ranges remain otherwise unchanged.

**Original rationale.** Repeated colors were already desirable and common in
version 2, but the 30% canonical branch has unique colors and random generalized
draws did not create a lesson-level guarantee.

**Alternatives considered.** Force two named positions to the same color, or
sample colors and reject unique assignments. The pigeonhole guarantee is
simpler and preserves random placement of repeated values.

**Probe.** The one-mark-per-color rival survived 19/598 baseline windows in each
band. It survives 0/598 revised windows.

**Failure modes and limits.** Repeated colors do not by themselves identify
reflection geometry, so this witness is combined with the existing far/near
positions and the row/column witnesses.

## D4: Declare executable competitors and witnesses

**Input choice.** Add three task-specific rivals, three witness predicates,
rival/witness links, and a lesson-level identifiability hook.

**Original rationale.** Unknown; the imported generator declared only
`strict_canonical_like`. The shared semantic gate supports richer declarations,
but cannot infer arbitrary task-specific wrong programs safely.

**Alternatives considered.** Document the risk only; encode assertions solely in
unit tests; or expose it to both unit tests and the shared semantic gate. The
last option was selected because it produces retained per-band evidence and
checks materialized lessons.

**Probe.** The after semantic gate verifies 60/60 sampled witness/rival claims
for each competitor and 12/12 identifiable lessons.

**Failure modes and limits.** A rival can be observationally equivalent to the
authority on the lawful grammar. Such a hypothesis should be marked
`authority_equal`, not treated as a data defect. This is why whole-grid-center
reflection was not added as a failing rival.

## D5: Keep dimensions, panel grammar, and overrides unchanged

**Input choice.** Preserve `grid_h=5..16`, `panel_w=3..8`,
`palette_size=3..5`, centered divider, empty right panel, and canonical profile
set. Explicit overrides continue to force generalized generation.

**Original rationale.** These are the already reviewed observable axes and
lawful input domain. Changing them was not needed to repair the lesson defect.

**Probe.** Override, distribution, diversity, self-check, and profile-floor
stages all passed after the edit. The profile floor still sees canonical support
in every band.

**Failure modes and limits.** Off-center dividers or pre-populated right panels
could separate additional hypotheses, but would change the task grammar and
were deliberately excluded.

## D6: Do not edit the Racket rule

**Input choice.** Retain the canonical Racket source exactly.

**Original rationale.** Prior authority evidence found the selected program
synchronized with the canonical record and executable on all canonical pairs.
The larger archival source is intentionally retained as provenance despite its
textual divergence.

**Alternatives considered.** No semantic defect was found in the rule, so any
rewrite would add source churn without improving labels.

**Probe.** Rule smoke, grammar, Racket lint, authority sync, and execution parity
all passed after the generator change.

**Failure modes and limits.** The rule remains defined somewhat beyond the
teaching grammar, while `self_check` owns the narrower input distribution. That
separation is intentional and tested.

## D7: Add task-local regressions and reusable census evidence

**Input choice.** Add tests for every three-demo window, every generalized
witness, and the lesson hook; retain a standalone before/after census script in
`checks/shortcut-census/`.

**Original rationale.** Existing tests covered determinism, canonical pairs,
structural validity, dimensions, palettes, overrides, and broad witnesses, but
not lesson-level survival of canonical-specific rivals.

**Probe.** Each new API was introduced after a failing test. The final task-local
suite passes 12 tests, and the inherited after battery passes all 12 stages.

**Failure modes and limits.** The task-local pytest suite is not currently
invoked by the inherited battery; this is reported separately in
`FEEDBACK_TO_CODEX.md`.
