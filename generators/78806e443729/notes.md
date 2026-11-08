# Working notes: 78806e443729

## Current decision

Keep the approved production generator and canonical rule unchanged. The native
parameter is episode-fixed `beam_mode` with exact canonical/default
`horizontal_only` behavior and alternate `dominant_relay` behavior.

`dominant_relay` is deliberately compositional: run the canonical horizontal
beam transform, select the unique modal nonzero color in that intermediate and
recover its original seed, then cast that color vertically through cells that
were zero in the input until an original seed or boundary. Globally unique input
seed colors make the selection genuinely dependent on the horizontal result;
before step A all colors occur once.

## Supported family

- Deterministic, matched inputs across settings.
- Independent 2–6 demonstration and 1–4 query requests; qualification uses 3/4.
- Four distinct stored queries with the same first query under one-query use.
- Sequential public turns reveal one query input only and expose no setting,
  seed, program, future query, query count, or query answer.
- The first query is a constructive 30×30 case spanning all boundaries and all
  four quadrants, with both dominant sides and blocker/no-blocker cases elsewhere.

## Retained evidence

- Production generator SHA-256: `4f4be058cd32d55b568086348d39e5003e20d39129dce53ec8900179434f8f46`.
- Exact canonical/default Racket SHA-256: `65a855ce11f7677687180f9efce9eaa4d834294153ea86cdc41c0a88e911ad02`.
- Alternate Racket SHA-256: `fd891abb3c01684a8f3813cb49de80a1a949a12dad5c764fea37664e5ba64fea`.
- Prototype manifest SHA-256: `417bfd62f2f5398fd4b2af8c5d4d54c335cccb836dd258be971e5fb1b16e9143`.
- Final staged tests: 35 passed; focused native tests: 27 passed.
- Teaching audit: both settings, 3 demonstrations, 4 queries, protected Racket,
  and five executable rivals per setting; every rival fails the demonstrations.
- Reliability sweep: 50 seeds, all demonstration counts, 500 episodes, 4,000
  visible pairs, 250 matched-input comparisons, and 2,000 public turns.
- Native qualification: 4/4 jobs across both settings and seeds 0 and 17; exact
  execution receipt SHA-256 `48ee53e33d6ffa212e83d31a4a6862165762bf36d8962ccc12ad7a2d2819df1b`.
- Causal witness SHA-256: `a335d7f85c2d87af5f3423b30f1ea5ca98718cc4c7dc762d383ccfa296ac98d0`;
  an independent replay also passed.

The source-bound witness uses the qualified 30×30 alternate query. Correct A
selects color 4 with a 28-cell beam at `[20,27]`; the wrong-intermediate
counterfactual selects color 3 with a 2-cell beam at `[20,1]`, changing the final
protected-Racket output.

## Review findings and limits

The bundled baseline task test initially depended on the legacy
`scripts.coder_synth_verify` namespace and a fixed `parents[1]` root. It was made
portable with `reviewer_support` and `RacketBridge`; production semantics were
not changed. The teaching audit is a bounded rival set, not a universal proof.

## Next action

The owner should integrate these exact bytes, rerun native qualification and the
source-bound witness replay, then execute native acceptance. `training_admitted`
remains false. Optional peers `7fc997c58be3` and `7aee010af40d` were not run.
