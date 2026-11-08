# Working notes: 1d62131e83ca

## Current decision

Keep the approved production generator and canonical authority unchanged. The
small proposed extension lives only in `workspace/parametric/` and adds one
episode-level parameter:

- `ray_orientation=nw_se` (default): exact canonical blue up-left / red
  down-right rays.
- `ray_orientation=ne_sw`: blue up-right / red down-left rays from the
  corresponding outer block corners.

The setting is fixed once per episode. The prototype samples only the common
collision-free support where both settings are lawful and produce different
answers. Retained episodes use 3 demonstrations and 4 distinct queries, while
the API accepts independent exact-integer counts from 1 through 8.

## Evidence retained

- `checks/parametric/1d62131e83ca-ray-orientation.json`: exact canonical text,
  all four canonical pairs, two 3+4 episodes, 32 Racket evaluations, intended
  Python/Racket parity, rival Racket/Python parity, demonstration refutation,
  query sensitivity, answer masking, and visible-only public IDs.
- `checks/parametric/1d62131e83ca-adversarial.json`: 24 deterministic episodes
  across easy/medium/hard, 168 pairs, 1/1 and 8/8 count boundaries, exact
  integer cells, common-support validity, and public/private identity attacks.
- `checks/1d62131e83ca-task-tests-final/result.json`: portable staged suite,
  11 passed.

The pre-existing task test initially failed in the copied runtime because it
looked for canonical data under the task directory. It now uses
`reviewer_support.find_root` and `canonical_pairs`; assertions and production
behavior are unchanged. The failed receipt remains under
`checks/1d62131e83ca-task-tests/`.

## Limits and next useful action

This is a proposed prototype, not approval or training admission. Exact-Racket
evidence covers two retained medium episodes; the bounded attack is finite and
checks only the declared two-setting rival plus sampler/privacy surfaces. A
maintainer considering promotion should decide whether the common-support
restriction is desirable and then run the normal production review for a
separately selected variant rather than silently replacing the canonical rule.
