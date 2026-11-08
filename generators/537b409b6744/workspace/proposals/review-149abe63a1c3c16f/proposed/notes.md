# Current notes: 537b409b6744

## Selected rule and authority

The modal color is background. Same-color 4-connected components form candidate
mover/wall pairs when a solid wall faces the mover, overlaps it on the transverse
axis, and is strictly wider/taller. The smallest axial gap wins; equal gaps prefer
the larger wall. The selected mover is erased, its channel through the wall is
cleared, the wall grows transversely around that channel, and the mover appears
on the far side. Output shape is unchanged.

Selected version: `4.1.0`. Declared rule hash: `7b81cecb3b71`. The canonical Racket
program was not edited in this review. Final generator SHA-256:
`34b8e36ac6bc1da85db025e34c4d908930dc5ce548cf3872e655312bb2e902cd`.

## Current generated domain

Helpful scenes use exactly four colors: a unique modal background, one solid
mover, one larger solid wall, and one farther differently colored candidate.
Directions, dimensions, gaps, palettes, wall/mover dimensions, and solid/ragged
distractors vary. Explicit public axes remain recoverable from pixels. Valid calls
require a literal integer seed, literal nonnegative integer sample index, and
`None|easy|medium|hard` difficulty.

Default mover depth is 2 on even sample indices and 1 on odd indices. Combined
with the existing distractor schedule, every four sequential lesson pairs contain
at least one larger-near/smaller-far example. This schedule is teaching support,
not an extra semantic rule and not a restriction on explicit overrides.

## Current semantic contract

Declared rivals and witnesses are:

- nearest candidate versus `farthest_pair`;
- wall growth versus `no_wall_growth`;
- nearest candidate versus the canonical-fitting `smallest_mover` shortcut.

`smallest_mover` chooses minimum mover area and uses canonical rank as a tie-break.
It fits all 8 usable labeled canonical pairs, so it is also in
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`. The retained exact counterexample
is `counterexamples/smallest-mover-shortcut.json`; source-bound evidence is
`checks/shortcut/smallest-mover-evidence.json` in the return workspace.

## Verification

- Before source: 11/12 battery stages green; defect lint had 48 strict-scalar
  warnings.
- Final source: 12/12 battery stages green; 600/600 strict semantic draws; all 8
  canonical inputs accepted; smallest-mover witness 317/600; 31,230 override
  draws with zero findings/warnings; exact-profile support 6/20 easy, 6/20 medium,
  7/20 hard.
- Portable selected task tests: 90 passed.
- Source-bound lesson census: 300 three-demo/one-query lessons, 1,200 unique
  inputs, 0 production ambiguities and 0/1,200 query-rotation ambiguities.

## Parametric assessment

A separate proposed prototype under `workspace/parametric/` varies
`candidate_selection` between `nearest` (canonical default) and `farthest`, once
per episode. It preserves object roles and every transformation after selection.
The evidence contains two complete Racket-labeled episodes, 16 executions, and
six distinguishing demonstrations. It is not selected, approved, or on the
production path.

## Decisions and reversals

- **v3.0.1 → v4.0.0 (prior return `review-84d80652cf29f872:v0001`):** replaced a
  two-object/background-0 toy distribution with ranked three-object scenes,
  observable exact axes, varied semantic colors, structural validation, and
  declared nearest/no-growth rivals. That return's notes were used as leads, not
  as measurements of this packet.
- **v4.0.0 → v4.1.0 (this review):** added strict invocation validation; reversed
  the claim that no canonical-fitting shortcut exists; declared and taught
  `smallest_mover`; retained the canonical Racket rule unchanged.

## Known limits and open questions

The helpful sampler intentionally covers 10--14 grids, mover spans/depths 1--2,
wall extras/depths 2--3, and gaps 0--2 rather than every canonical-lawful geometry.
`self_check` accepts broader canonical cases. Finite declared-rival and generic
searches do not prove unique induction against every possible hypothesis. The
new parity schedule is a deterministic authoring mechanism, not a claim that
sample-index parity has puzzle meaning. No canonical-repair blocker remains.
