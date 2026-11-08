# Working notes: c6a422753abe

## Review diagnosis

The imported generator created both a full blue row and a full blue column,
then reflected a source into three quadrants. The selected authority instead has
one separator line and one reflection. Because the baseline sampled a different
puzzle, incremental tuning would have preserved mislabeled examples; the
sampler, mirror, validator, and tests were replaced together.

## Canonical repair

Version `3.0.0` now enforces:

- exactly one full blue row xor one full blue column;
- a connected two-color source entirely on one side;
- an empty reflected side and in-bounds one-step reflection;
- canonical source-color swap with an unswapped reflected copy;
- exact override handling, input-pure `rule_mirror`, and semantic lesson checks;
  and
- dimensions from 8×8 through a substantive 30×30 case.

The focused task snapshot passed 27 tests. A deliberate lint RED found a missing
`RULE_HASH` declaration and two unprobeable axis descriptions; after correcting
those declarations, lint passed with zero errors and warnings. Focused
self-check and Racket lint also passed. The canonical rule hash is
`1781c378782f`.

## Current parametric proposal

The task-local adapter proposes `swap_location = source | reflection`. The
default `source` source is the selected canonical Racket program byte-for-byte:
swap the original shape and paint an unswapped reflection. The alternate keeps
the original unchanged and swaps only the reflection. Separator geometry,
reflection, palette membership, source connectivity, and the public input
grammar remain invariant. Every supported 2–6-demo prefix identifies the
setting before four independently sampled queries are exposed.

Protected replay covered 18 jobs across both settings, seeds 0/17/91, and demo
counts 2/3/6. It verified 138 pair labels in 204 Racket evaluations, checked
same-seed public-input invariance, and retained a 30×30 query. This is
reviewer-reported proposal evidence only; no owner qualification, acceptance,
production promotion, or training admission occurred.

## Remaining diagnostic and next action

The selected `target_code` remains textually different from the canonical copy,
while execution parity passed over the two source texts. Shared authority
normalization is owner-scoped and was left untouched. The next useful action is
to decide whether to synchronize that authority text, then run owner
qualification on the finite two-setting family.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
