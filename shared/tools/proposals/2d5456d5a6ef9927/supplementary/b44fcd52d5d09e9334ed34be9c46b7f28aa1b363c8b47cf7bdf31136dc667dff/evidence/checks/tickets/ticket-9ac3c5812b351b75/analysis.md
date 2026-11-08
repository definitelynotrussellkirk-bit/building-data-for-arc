# Bounded allocation-quality audit

Ticket `ticket-9ac3c5812b351b75`; seed
`cc9d66bd9447da723da53f0d35e903168d720c7dfa6f2fbb1b657d3fd566da8d`.
This is a proposal/evidence ticket, not a mixture change or training-admission decision.

## Current bindings and allocation surfaces

- The ticket's pinned source `repo/generators/1856980929fe/generator.py` still has SHA-256
  `513b681db0dfd9c530f867d70905b082bd14353d2d2c4b77484b2bbe529da7ea` and rule hash
  `77504f6c55fa`. Its current review index contains an unresolved, source-matching teaching
  counterexample: under one direct five-demo schedule, a two-seed-cap rival fits every demo
  and changes a three-seed query. This is evidence that approval alone is not a sufficient
  allocation weight.
- The packet's authoring draw has 154 normal IDs and a separate 1/10 evaluation-focus branch
  with only two eligible related generators. Its own scope says this is authoring focus, not
  training admission or difficulty calibration.
- In the packet catalog, 298/300 records have `mix_weight=1.0`; only two unreviewed generic
  records have weight zero. Thus the present catalog surface is almost uniform rather than
  evidence-weighted.
- The October 23 training snapshot reports a different layer: uniform ARCpuzzles generator
  defaults with four queries, and materialized token shares ARCpuzzles 37%, NVARC 36%,
  ARC-GEN 16%, RE-ARC 11%. Those dated realized shares are not the packet's authoring draw
  probabilities and are not measured optima.

## Seeded three-record sample

Sampling algorithm:
`random.Random(int(ticket_seed, 16)).sample(sorted(packet_generator_ids), 3)`.
One medium episode per record used the declared demo minimum (floor 3) and four shared-demo
Racket-labelled queries. All source and executed-rule hashes matched the packet bindings.

| Task | Current status | Live episode | Representation | Teachability evidence | Cost |
| --- | --- | --- | --- | --- | --- |
| `27a915a2c9b3` | packet unapproved; catalog `reviewed_standard`, review status `improved` | 4 demos + 4 distinct queries, 8/8 distinct inputs, 0 sampling rejections | sides up to 27; one observable `scene_profile` axis; exact and generalized profiles appeared | no `lesson_identifiable` hook and no current review index; historical notes report broad morphology tests but do not certify four-query identifiability | 3.685 s |
| `d07c7972d183` | packet approved; `reviewed_safe`, accepted repair | 3 demos + 4 distinct queries, 7/7 distinct inputs, 0 sampling rejections | sides up to 13; observable height/width/period controls | no runtime hook, but current notes retain a 12/12 battery, duplicate-rejection integration test, Racket parity, and finite declared-rival/query-rotation censuses; the old top-left audit is bound to stale pre-repair bytes | 4.028 s |
| `260f488cb5a8` | packet unapproved; `provisionally_safe` | 4 demos + 4 distinct queries, 8/8 distinct inputs, 0 sampling rejections | sides up to 9; four scheduled profiles and exact height/width/profile controls | all four live queries returned clear from the declared eight-rival hook; associated notes retain source sync, negative recombination, profile and semantic evidence | 4.606 s |

Measured raw yield was 3/3 complete episodes, 12/12 distinct labelled queries, and zero
sampling rejections in 12.35 seconds. That is encouraging for execution reliability, but only
2/3 records have current source-bound lesson evidence sufficient to score teachability in this
bounded inspection (`d07...` via retained census, `260...` via live hook). The only sampled
large-grid record is the one with the largest teachability-evidence gap, so filtering solely by
review status would damage representation.

## ARC-GEN and RE-ARC evidence available in this packet

No current generated summary from either source is shipped, so their reported 16% and 11%
token shares cannot be converted into quality-per-cost measurements here.

- `repo/shared/tools/build_arc_native_dataset.py` can require a rule-backed task, validate
  every grid against canvas/color bounds, tensorize rows, group up to four queries, and record
  per-task, bounds and tensor failures. It does not itself establish lesson identifiability;
  a source summary with rejection/failure and four-query counts is needed before increasing
  volume.
- `repo/shared/tools/integrate_re_arc.py` hashes generator/verifier source, requires verifier
  agreement, drops identity pairs, deduplicates pairs, caps search at 25 attempts per requested
  pair, and skips keys with too few verified examples. Its CLI defaults to one to three queries;
  the dated training context does not say whether four was configured. It uses Python verifier
  consistency rather than a Racket authority receipt. These are useful quality controls, but
  no current rejection, skipped-key, grammar, or ambiguity distribution is present here.

## Alternative allocation: evidence-tiered ARCpuzzles pilot

Keep the global source-token shares unchanged for the pilot. Within only the ARCpuzzles slice,
compare uniform generator sampling against this bounded alternative:

1. Weight 2.0: current source/rule hashes, no open source-matching safety finding, Racket
   four-query receipt, and current source-bound lesson evidence (live hook or retained census).
2. Weight 1.0: current source/rule hashes and Racket four-query receipt, but lesson evidence
   incomplete; retain these for exploration and representation.
3. Weight 0 for training minting (not authoring/review): stale source binding, label failure,
   or open source-matching safety finding until assessed.
4. Reserve at least 15% of ARCpuzzles episodes for records whose validated input or output has
   a side of 20–30, and cap each task at 0.25% of the pilot, preventing the quality gate from
   collapsing large-grid or task diversity.

This alternative is expected, not measured, to raise teachability-verified episodes per Racket
second because it avoids spending labels on stale/open records, while the explicit large-grid
quota protects the failure exposed by the three-record sample.

### Bounded test and stopping rule

Use a fixed source/rule snapshot and one seed to sample 100 tasks. Mint two arms of four episodes
per task (800 total episodes): baseline uniform and alternative weighted, each with independent
3–5 demos and four distinct queries. Record source/rule freshness, Racket success, duplicate and
other rejection counts, tensor/grammar failures, declared-rival survival, elapsed seconds,
large-side share, task coverage, and visible challenge hashes.

Define a usable episode as: current source/rule binding, four distinct labelled queries, no
label/tensor/grammar failure, no surviving declared rival when a current check exists, and no
unresolved source-matching safety finding. Promote the alternative only if it yields at least
10% more usable episodes per Racket second, keeps unique-task coverage within 5% of baseline,
keeps side-20–30 representation within 2 percentage points of the 15% floor, and introduces no
new source-specific failure mode. Stop early after 200 episodes per arm if the alternative is
more than 10% worse on usable yield or violates either representation bound. Otherwise stop at
800 episodes; do not infer a global source-share change from this pilot.

## Coverage limits

This audit sampled three ARCpuzzles records and one episode per record. It did not run models,
a corpus-wide battery, or fresh ARC-GEN/RE-ARC/NVARC jobs. Declared rivals are finite; no hook is
not proof of ambiguity, and a clear hook is not a proof of unique induction. Local elapsed times
are rough execution-cost observations, not production throughput estimates.
