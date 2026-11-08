# Working notes: e9238d278276

## Current decision

Keep the production generator and canonical authority unchanged. The completed
native sidecar lives under `workspace/parametric/` with episode-fixed parameter
`gravity_policy`:

- `all_up` is the exact canonical default: pack every column's nonzero cells
  upward while preserving their original top-to-bottom order.
- `signal_ranked_down` locates the unique active column containing only color 9,
  counts its nonzero cells, uses that count as a one-based rank among all other
  active payload columns from left to right, applies canonical upward gravity to
  every column, and then repacks only the selected payload column downward while
  preserving its original value order.

The input scene is independent of the private setting. The family supports 2–6
demonstrations and 1–4 independently requested, prefix-stable queries. The four
query constructions are 14×16, 19×21, 24×27, and a substantive 30×30 case.

Canonical program SHA-256:
`e1b2d0d818580bce5a559db3c731bcd94591afb3af0ba32d9757c0d821a86fcb`.
Alternative program SHA-256:
`7fdb2f65cbea703e6f55511229d92d1f5b501ac443b7db3bb45fb924879983c8`.
The unchanged production generator SHA-256 is
`4f8315cf1cccc08a6944643a59c9d492ccba6c277a3af16ccbded3d8f2bab15e`.

## Teaching and evidence

The first two demonstrations use signal ranks 2 and 4. They distinguish the
settings and reject canonical-only, all-down, fixed-rank, reverse-rank,
signal-position/modulo, longest/shortest-column, and selected-value-sorting
shortcuts. The reusable `workspace/parametric/audit_lessons.py` checks count
boundaries, setting-neutral inputs, query-prefix stability, public masking,
exact 30×30 coverage, and the declared rival bank.

Current evidence:

- copied-runtime task suite: 28 tests passed;
- bounded audit: 192 episodes over 32 seeds, 192 exact 30×30 pairs, 736
  setting-dependent answer differences, zero construction failures, and zero
  surviving declared rivals. A larger 64-seed invocation exceeded its wrapper
  budget and is not reported as a passing check;
- native qualification: both settings at seeds 0 and 17, four jobs and 40
  protected-Racket evaluations, execution SHA-256
  `9d9286f24b55841badc066d412c96df0c5a6dc3f8fba94118679d39483e9741d`;
- sequential public projection: 16 one-query files verified for source binding,
  masking, exact visible-byte IDs, schema, and duplicates;
- protected-Racket counterfactual: replacing measured rank 3 with rank 1 on the
  same qualified input changes which payload column is down-packed and changes
  the final output. Witness SHA-256
  `7497410d34fd8dbb6d18c29eb28fb007c05c50e4de88cc6c81597e50fe70d143`;
  replay status is `reviewer_replayed`.

The copied-runtime suite emits one legacy-namespace warning from the inherited
canonical-profile test; it does not affect the 28 passing tests or the native
source binding.

## Limits and next action

This is finite reviewer evidence, not a universal uniqueness proof or measured
training gain. The current manifest deliberately leaves `variant_approved` and
`training_admitted` false. Owner integration must preserve these exact bytes,
rerun native qualification and the causal witness, perform fresh acceptance,
and explicitly admit training. No production rule or generator change should be
made merely to adopt the sidecar.
