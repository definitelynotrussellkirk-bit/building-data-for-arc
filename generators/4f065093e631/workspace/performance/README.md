# Equivalent frame-rule performance repair

`optimized_rule.rkt` replaces repeated rectangle-cell allocation with prefix
counts and necessary-corner filters. It preserves the complete frame rule,
including equal-area frame selection and first-target behavior. The probe uses
the included protected Racket bridge; it does not substitute Python labels.

## Retained source identities

| Source | Exact SHA-256 | Whitespace-normalized SHA-256 |
| --- | --- | --- |
| `baseline_canonical.rkt` | `413d0d4e64d15f0a359af88b485014ce243ebb54257ff19147c0f848e8e14cb0` | same |
| `baseline_archival.rkt` | `39476dda0e838d20ffadb423794a33aa3f50ffcbe38ba776b1599a5ccf711afa` | `04dc58ab5b0ed9048b0c9b19eb6fc5583f61fac391583ab74b2e22bbcf59db96` |
| `intermediate_prefix_only.rkt` | `3aa2a93dadb93db6e7ce02bebca093157233b7aca4fddac6881b104d708821b4` | `c5d40737bb65fafdcb7094fb8ea8490f2536b775d2ca224098d43f3882f1ec09` |
| `optimized_rule.rkt` | `94d39e6bd6527f33f02f7d14f573a1627c4025bb1ca3f4e57aff87aff75603dc` | `6d3fbf3d14b412c33062680c91df351841646735f08ae2413794ae0a83a4ccf5` |

The canonical fixture is the exact original `program_solution` for task
`4f065093e631` in `shared/data/canonical/puzzles.jsonl`. The archival fixture is
the exact original `racket_target.raw_code` in
`shared/data/base/solutions/training/890034e9__4f065093e631.json`; its original
`target_code` was byte-identical. Their alias differences were not a prior
optimization. Preserve archival `raw_code` unchanged when updating active
authority.

The 13 generated inputs were captured from original generator SHA-256
`ecc388975e999108832bff4d4bf8ab788f2583152a40a392b26cd5c626daa836`.
The retained inputs, seed/index/band/override settings, hashes and exact outputs
make these comparisons replayable after later generator edits.

## What failed, and what was reproduced

The before-battery lint log reported seed 4 producing only 3/5 pairs after
25 attempts. Its temporary rejected-record file showed a 10-second evaluation
timeout at seed 4/index 3, followed by startup handshake failures. The temporary
file was removed by the completed battery before it could be copied; the
observed excerpts and this provenance limitation are recorded honestly in
`checks/performance/baseline_provenance.json`. The primary lint log remains at
`checks/before/checks/4f065093e631_before_lint.log`.

**That exact regenerated seed-4/index-3 input did not deterministically time
out in isolation.** It completed in 0.588 seconds on a fresh original bridge,
and 0.545 seconds in the larger comparison. We therefore do not identify one
deterministic input as the sole cause of the original battery failure.

A separate constructed 30×30 input supplies a valid tall frame, another
same-sized zero-interior slot, and all nine nonzero colors. The original rule
timed out at the unchanged 10-second budget. A diagnostic run with a 60-second
budget obtained its original output in 18.592 seconds; the optimized rule
produced exactly that output in 0.104 seconds. The optimized rule also passed
the normal 10-second budget independently. The longer diagnostic budget was
used only to obtain the old rule's comparison output; no production timeout
was raised.

This constructed witness belongs to the broad Racket rule domain, but its
30×30 size and ten-color palette are outside the calibrated 21×21/four-color
generator distribution. See `counterexamples/performance_timeout_30x30.json`.

One planned comparison failed before the payload started: `setup_racket.py`
timed out after 20 seconds while running only a Racket readiness probe. Its
traceback is retained in `checks/performance/stress_wrapper_failure.txt`; the
fresh retry completed. Startup failures are infrastructure evidence, separate
from rule-evaluation correctness and timings.

## Why the change preserves the rule

1. For each present color and zero, a prefix table counts that value in every
   half-open rectangle. Four table reads give the exact count in any requested
   rectangle. An interior is all zero exactly when its zero count equals its
   area. A border is monochrome exactly when the outer rectangle's color count
   minus the interior's color count equals the border's cell count.
2. Every corner belongs to a candidate frame's border. The new guards skip only
   candidates whose corners already disprove a monochrome border. They retain
   the relative order of every candidate that could be accepted.
3. The original sorted color order and `color, r0, r1, c0, c1` nesting remain.
   Accepted frames are still accumulated by `cons` and sorted stably by
   descending area. Thus every equal-area tie is preserved, including the
   reverse enumeration order produced by `cons`.
4. The zero-slot predicate is equivalent, and slot order, source-slot exclusion,
   `(target (fst slots))`, and the final `paint-cells` expression are unchanged.
   The parametric materializer's exact replacement fragments remain unique.

The original implementation constructs every interior's coordinate list before
testing its cells. Across all candidate rectangles that entails
`K * choose(H, 3) * choose(W, 3)` coordinate pairs, where K is the number of
nonzero colors: 148,352,400 pairs for the wide-palette 30×30 witness. Prefix
tables require O((K+1)HW) preprocessing/storage; rectangle tests are constant
time and corner filters discard impossible candidates early. No input palette,
size or sampling restriction was added. Empty/no-frame inputs remain errors.

## Bounded comparison evidence

`checks/performance/differential_26_cases.json` records **26/26 matching inputs
across three Racket sources**, with 78 successful evaluations and no expected
output mismatch. It covers all four canonical anchors; twelve generated draws
covering four profiles in each of easy/medium/hard; the reported seed/index;
and nine independently constructed smallest, boundary, dense, multiple-target,
smaller-distractor and equal-area cases. Generated seeds are 4000–4003,
4100–4103 and 4200–4203, with corresponding sample indices 17–20. Each exact
profile override is retained in `checks/performance/cases.json`.

`checks/performance/differential_stress_retry.json` adds one distinct stress
input, matching the original and optimized rules. This is 27 distinct inputs in
total; it is finite evidence, not an exhaustive grid census. The equivalence
argument above explains the general predicate/order preservation.

Representative measured evaluation times (one observation per source/case;
startup excluded, wall-clock contention possible):

| Input | Original canonical | Optimized | Evidence |
| --- | ---: | ---: | --- |
| Canonical train 0 | 0.410018 s | 0.071095 s | `differential_26_cases.json` |
| Reported seed 4/index 3 | 0.544874 s | 0.063452 s | `differential_26_cases.json` |
| Dense 30×30 | 6.243457 s | 0.149193 s | `differential_26_cases.json` |
| Tall 30×30 | 7.149173 s | 0.067545 s | `differential_26_cases.json` |
| Wide-palette tall 30×30 | 18.592250 s | 0.103885 s | `differential_stress_retry.json` |

The prefix-only intermediate took 4.288 seconds on the stress case. Its source
and result are retained to identify that earlier measurement accurately; the
final candidate additionally applies necessary-corner filters.

## Mirror tie regression

The original Python mirror chose the wrong source on two retained equal-area
cases even though its calibrated generator always required a unique largest
frame. The smallest witness is 6×9: a color-4 3×3 frame at (0,0)–(2,2) and a
color-8 3×3 frame at (3,6)–(5,8) on nonzero checkerboard noise. Both Racket
baselines choose color 8 and repaint the first frame. The old Python mirror
chooses color 4. A second witness distinguishes equal-area frames of different
dimensions at different top rows.

For frame tuples `(color, top, left, bottom, right, area)`, the equivalent
descending comparison key is `(area, color, top, bottom, left, right)`.
`checks/performance/mirror_ties_red.xml` retains the pre-repair result: two
failures and one passing control. The exact grids and Racket/Python outputs
are in `counterexamples/performance_tie_order.json`. The final focused receipt
records the rerun after the coordinator's Python-mirror fix.

## Run the tools

From the outer packet directory, using the prepared isolated interpreter:

```bash
WORK/.venv/bin/python review.py run "$PWD/WORK/.venv/bin/python" \
  generators/4f065093e631/workspace/performance/probe_rule.py probe \
  --cases ../checks/performance/cases.json \
  --rule generators/4f065093e631/workspace/performance/baseline_canonical.rkt \
  --rule generators/4f065093e631/workspace/performance/optimized_rule.rkt \
  --timeout 60 --out ../checks/performance/new-comparison.json

WORK/.venv/bin/python review.py run "$PWD/WORK/.venv/bin/python" \
  -m pytest generators/4f065093e631/tests/test_rule_performance.py -q
```

Choose a new report path for each invocation; the probe refuses to overwrite
retained evidence. `capture --out NEW.json` creates a new source-bound case
corpus from the current generator. The focused tests assert exact outputs on
canonical and constructed inputs and the Python mirror's tie behavior. They
contain no wall-clock performance threshold.

The final focused run passed **18/18 cases, with no failures, errors or skips**
on generator SHA-256
`bbefdd3a1318c5fc34cfc1297eb6105f1b0eccd7ca99694e8930702ba748a5de` and the final
Racket candidate above. Its JUnit receipt is
`checks/performance/unit_tests_final.xml`. Compact counts, limitations and
12 actual command/exit/evidence records are in `checks/performance/SUMMARY.json`
and `checks/performance/RESULTS_fragment.json`.

The ordinary lambda fixtures execute through public `strip_rule_wrapper` and
`RacketBridge`, bind their own height/width, and use no dictionary or shorthand
syntax. The more general `wrap_rule` authoring helper currently imports the
absent `scripts.comment_solutions` namespace in direct repository layout;
`checks/performance/wrap_rule_authoring_failure.txt` retains that independent
shared-tool issue. No private runner functions or shared-runtime edits are used.

## Active-authority integration

Use the exact final candidate text for the selected canonical row's
`program_solution` and the selected base artifact's `racket_target.target_code`.
Leave `racket_target.raw_code` at its archival hash above. Set the generator's
`RULE_HASH` to `6d3fbf3d14b4` only after validating those exact bytes. Do not
refresh approval metadata on this evidence alone. Rebuild the parametric
prototype's settings from that selected text, then run the ordinary authority
and task-test checks in the coordinator's final workflow. These local fixtures
and bounded comparisons do not substitute for final packet replay.
