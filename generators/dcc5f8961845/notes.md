# Current notes: dcc5f8961845

## Selected source and parametric decision

The selected production generator remains byte-identical at SHA-256
`1bf0ed962c3e1e98187d3fad584489823b420f8f2a8b483dfb8fb973d316c965` and
canonical rule hash `9f952248bd5f`. The native prototype adds one episode-fixed
parameter, `second_source`, while preserving the exact canonical Racket bytes as
the default:

- `header`: apply the two transform commands stored in input cells `(0,0)` and
  `(0,1)`; the program SHA-256 is
  `06fb16f2c8eda92699aa13c4be90f3463597512f9430030ac511acf130c17003`.
- `post_first_marker`: apply the first header transform, observe which corner
  contains the unique color-9 marker in that transformed motif, and choose the
  second transform that moves that observed corner to top-left; the program
  SHA-256 is
  `9ef255b8e4bb356d40d274752334e65f61d2be28514c047b56a1b707b8893457`.

This is a genuine sequential dependency: step B cannot be selected before step
A produces the transformed marker corner. The task-local protected-Racket skip-A audit remains in
`workspace/parametric/evidence/current/racket-review/causal-witness.json`.
The admission-contract witness, copied from the exact qualified pair and replayed
through the protected runtime, is `checks/dcc5f8961845/causal/witness.json`.

## Lesson construction and repair

The adapter supports two through six demonstrations and one through four
queries, with four distinct queries in the normal export. Inputs are matched
across settings, first-turn prefixes are stable, and the fourth query is a
substantive 30x30 boundary case rather than padded small content.

The first protected-Racket teaching audit found a real shortcut:
`header_then_marker` fit both initial demonstrations while changing query
answers. The Python audit also incorrectly removed equal-output rivals before
checking whether they fit. A regression first exposed that checker defect; the
audit now retains every rival, and the two constructive demonstrations were
changed from command pairs `(1,5)/(3,4)` to `(1,3)/(2,1)`. This repaired the
hole without increasing the demonstration count.

## Verification and handoff

- Native qualification: `checks/dcc5f8961845/qualification/qualification.json`
  is `qualified` for both settings, seeds 0 and 17, two demonstrations and four
  queries; sibling `execution.json` records 32 protected-Racket evaluations.
- Focused task tests: 53/53 passed in
  `checks/dcc5f8961845-tests-final/result.json`.
- Extended self-review: four matched episodes, 146 protected-Racket executions,
  finite rival audit, projection checks, and the skip-A witness passed.
- Bounded sampler sweep: 64 seeds, 640 episodes, all demo counts 2--6, zero
  failures, all 36 header command pairs and 16 marker-corner transitions covered.

The prototype is reviewer-ready only. It is not owner-accepted, variant-approved,
or training-admitted. The next action is to integrate these exact source bytes,
then rerun native qualification and fresh owner acceptance on the live tree.
