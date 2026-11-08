# Working notes: f13d23b71bd4

## Current decision

Keep the production generator and canonical authority unchanged. The active
native sidecar is now the signal-ranked family under `workspace/parametric/`;
the older scalar `minimum_fall_size` prototype remains only as retained history.

The episode-fixed parameter is `fall_policy`:

- `all_large` is the exact canonical default. Every monochrome 4-connected
  object with at least four cells falls to the bottom on a fresh color-7 canvas.
- `signal_ranked` measures the unique color-1 signal object's cell count, treats
  it as a one-based rank among large non-signal objects in row-major component
  order, and drops only that selected object.

Both settings receive identical scenes. The family supports 2–6 demonstrations
and 1–4 independently requested, prefix-stable queries. Four distinct queries
are retained, including a substantive 30×30 scene.

Canonical program SHA-256:
`71a162d2019efc9e1dad31b9b6f99b2a6f80089126ad749ee444696b61efbf45`.
Alternative program SHA-256:
`03e3d26daee484783ae2e37bdf58fbfb26216efb66daff178cd7a36ee3047dc6`.
The unchanged production generator SHA-256 is
`5b2f9dfdf528813ad9d342a086943138201231be812b77fcf135c510c57b2b32`.

## Teaching, export, and evidence

The first demonstrations use different signal ranks and contain multiple large
objects, small distractors, repeated colors, boundary contacts, and ordering
traps. The reusable `workspace/parametric/audit_lessons.py` checks supported
count boundaries, setting-neutral inputs, query-prefix stability, exact 30×30
coverage, public masking, and a declared rival-rule bank.

The previous public-emission-order hold is resolved by
`workspace/parametric/public_batch.py`: it constructs every visible payload
first, hashes only exact public bytes, rejects duplicate visible identifiers
before creating the destination, and writes files in public-ID order. Private
settings, seeds, programs, answers, and future queries never enter public files
or identifiers.

Current evidence:

- copied-runtime task suite: 42 tests passed;
- bounded audit: 384 episodes, 384 exact 30×30 pairs, 1,472
  setting-dependent answer differences, zero construction failures, and zero
  surviving declared rivals;
- native qualification: both settings at seeds 0 and 17, four jobs and 40
  protected-Racket evaluations, execution SHA-256
  `28905e75f9e5f6149c9ca97cbf820b871704db2c79943dd0f1ae75380a60fd66`;
- sequential public projection: 16 one-query files verified for source binding,
  masking, exact visible-byte IDs, schema, and duplicates;
- protected-Racket counterfactual: replacing the measured rank with rank 1 on
  the same qualified input selects another large object and changes the final
  output. The replay status is `reviewer_replayed`.

## Limits and next action

This is finite reviewer evidence, not a universal uniqueness proof or measured
training gain. The current manifest deliberately leaves `variant_approved` and
`training_admitted` false. Owner integration must preserve these exact bytes,
rerun native qualification and the causal witness, perform fresh acceptance,
and explicitly admit training. No production rule or generator change should be
made merely to adopt the sidecar.
