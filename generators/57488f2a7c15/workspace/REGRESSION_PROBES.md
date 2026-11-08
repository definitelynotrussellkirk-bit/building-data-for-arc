# Independent symmetry probes

The focused tests and census read the selected task source. They find their own
library or copied runtime through `reviewer_support.find_root(__file__)` and
read canonical pairs with the supported helper. Their color, occupancy,
transpose-pair, and orientation expectations come from grid pixels; they do not
call generator observers or predictors to decide the expected result.

The selected training distribution uses at least two nonzero colors and at
least one unpaired off-diagonal source. These are teaching choices, not limits
of the pure Racket transformation. A monochrome short line, a singleton, a
diagonal-only grid, and already completed grids remain lawful Racket inputs.
The law tests include fixed points outside the selected training distribution
and check idempotence by applying the actual Racket operation twice. They also
check all canonical labels, output symmetry, and preservation of source cells.

## Commands

From the extracted packet root, run all selected task tests with retained public
stage evidence:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 57488f2a7c15 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

For a direct focused run from the packet root (payload cwd is `repo`):

```bash
python3 run_with_racket.py python3 -m pytest -q generators/57488f2a7c15/tests
```

Run the ordinary-draw census against a new output path:

```bash
python3 run_with_racket.py python3 generators/57488f2a7c15/workspace/conflict_census.py --seeds 10000 --out ../checks/conflicts-after.json
```

This means seeds 0 through 9,999, `sample_index=seed`, no overrides, independently
in each of `easy`, `medium`, and `hard`. The census counts malformed grids,
non-square grids, no-op grids, conflicting transpose pairs, rejected inputs,
and execution errors. It records both per-band and globally deduplicated input
counts. At most the first three exact witnesses of each kind per band are kept
by default; large populations do not require saving every grid. Its first
conflict witness in each band is labelled with batched public `Catalog.apply`.

`--expect-violations` is for an intentional baseline diagnostic. A report still
says `violations_found`; the flag succeeds only when violations exist. Ordinary
mode exits 1 on any violation, while execution or provenance errors exit 2.
Reports refuse to overwrite an existing destination. The exact selected
generator, canonical ledger and task row, raw rule, probe script, and loaded
generator dependency hashes are retained with the actual command and cwd.
The public reference report separately hashes the wrapped callable; that hash
is deliberately distinguished from the raw canonical source hash.

## Baseline regression evidence

The pinned generator SHA-256 is
`525a5770fbca7fc5cee98cc5037f313dcf62d77ed87f854f91cd9b150d57657d`.
The lead was the retained, previously unverified audit
`review-9a173d367793b6e0:v0001` in `evidence/review_index.json`; the following
counts were independently remeasured from that exact selected source:

| Band | Draws | Conflicting draws | Accepted conflicting draws | Conflicting orbits |
| --- | ---: | ---: | ---: | ---: |
| easy | 10,000 | 1,453 | 1,453 | 1,474 |
| medium | 10,000 | 2,136 | 2,136 | 2,274 |
| hard | 10,000 | 1,662 | 1,662 | 1,713 |
| Total | 30,000 | 5,251 | 5,251 | 5,461 |

There were zero malformed, non-square, or no-op inputs, zero generator or
validator errors, and zero validator rejections. The population contained
29,440 distinct input grids across all bands. The first witness, easy seed 1
with sample index 1, has `(0,1)=9` and `(1,0)=8`; `self_check` returns `[]`.
Real Racket execution swaps these two colors, violating both preservation and
symmetry. The conflict census and exact reference output are retained at packet
path `checks/conflicts-before.json`.

The original 28 focused domain/law tests produced 19 failures and 9 passes
before generator edits. The actual wrapper command, payload directory, test
hash, XML counts, and log hash are in `checks/symmetry-domain-before.json`;
its `.log` and `.xml` companions preserve every observed failure. Override tests
were added after those baseline measurements to exercise the new exact-control
contract; they were not part of the original 28-test baseline.

An initial census attempt mistakenly compared the public API's wrapped-callable
hash to the raw canonical source hash. Its complete diagnostic counts and
explicit provenance error remain in `checks/conflicts-before-probe-error.json`.
The corrected complete baseline report is the `conflicts-before.json` run above.
The finite census establishes the stated sample counts and does not prove every
possible seed or every joint override combination lawful.

## Intermediate repaired-source measurements

On generator SHA-256
`1eeda46fe9d082b75511b8266f9588a72bf08e9ba083dabeb05c9ac29c8b5bb4`,
the 28 independent domain/law cases and 114 exact-control cases all passed:
**142 passed, zero failed, errored, or skipped**, in 8.13 seconds. Both the
initial and final source hashes match. The direct command was:

```bash
python3 run_with_racket.py python3 -m pytest -q generators/57488f2a7c15/tests/test_symmetry_domain.py generators/57488f2a7c15/tests/test_overrides.py --junitxml=../checks/domain-overrides-intermediate-2.xml
```

It ran from the packet root, with payload cwd `repo`, and exited 0. The retained
receipt, full log, and XML are `checks/domain-overrides-intermediate-2.json`,
`.log`, and `.xml`. The `intermediate-2` filename records its place in the review;
the receipt binds the exact source above, including its 18-position schedule.

The matching census is `checks/conflicts-after.json`, using the documented
30,000-draw command without `--expect-violations`. It exited 0 with status
`no_violations_found`: every band had zero conflicts, malformed grids,
non-square grids, no-op draws, self-check rejections, or execution errors in
10,000 draws. There were exactly 10,000 unique inputs in each band and 21,847
unique inputs across all three bands. This cross-band overlap means the 30,000
draws must not be described as 30,000 distinct examples. The canonical rule
hash remained `2b970065d6a3`.

The preceding test attempt on generator SHA-256
`1cab196cc09e0086db55d27ac347a56d7cff55fed7ea1633594864660f2aa7b4`
is retained in `checks/domain-overrides-intermediate-1.json`, `.log`, and `.xml`:
133 passed and 9 failed. Those nine failures were test-author mistakes: the
tests expected the literal text `incompatible_axes` in an exception message,
while the agreed structured-error contract exposes `exception.incompatible_axes`.
The corrected tests check a nonempty list or tuple of supplied axis names on the
raised `ValueError`. All input-feasibility and observable-control expectations
are unchanged.

## Final-source measurements

The final source SHA is `695c31b0bf2506cde10a9f240b78d59f1bb5efd85038186bc9f532d4305eeaa7`. `checks/task-tests-final/result.json` records the explicit isolated task stage: 155 passed, zero failed/errors/skips. Its runtime path is `/tmp/arcpuzzles-check-mei6pb0f`. The source-bound final census is **`checks/conflicts-final.json`**, not either predecessor file above: zero violations in 30,000 draws, 21,847 globally unique inputs, 10,000 unique per band. The full after battery is 12/12 green.

The final production census is `checks/lesson-census.json`: 300 ordered five-demo lessons, 100 per band, all 11 distinct rivals refuted, 1,800 globally unique labelled pairs. Query rotations remain diagnostic: 300/1,800 are ambiguous. `checks/short-lesson-prefix-final.json` reuses saved labels: 147/300 three-demo prefixes are ambiguous, versus 0/300 four-demo prefixes, with all rivals refuted in the four-demo prefixes. Five is conservative and is the declared contract; no four-demo counterexample is claimed.

Public generation/export ignore the task's demonstration declaration; use explicit `--train 5` / `n_train=5` to follow this review's contract. Existing-output refusal and initial missing-pytest evidence are retained separately. The final repository suite is 359 passed, three optional torch skips. The return's `RESULTS.json` and fresh-replay receipt give exact commands, source identities and relocation results.
