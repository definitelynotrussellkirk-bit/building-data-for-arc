# Zero-count threshold prototype

This is a **proposed task-local prototype** for `520fe6e64fb6` (original
training task `fc10701f`). It does not change the selected generator, canonical
Racket rule, approval, or training admission.

## Parameter and unchanged reasoning

`min_zeros` is the minimum number of original zero cells on an entire between
row or column that triggers connector painting. Allowed values are the integers
`1`, `2`, and `3`; the original/default setting is `1`. Booleans, floating-point
values, strings and unsupported integers are rejected.

The following reasoning remains unchanged at every setting:

1. Find the global bounding boxes of all original `9` cells and all original
   `7` cells, including disconnected or irregular markers.
2. Recolor original `9` to `7` and original `7` to background `6`.
3. Equal minimum columns select rows; otherwise select columns. No additional
   row-alignment requirement is introduced for the column branch.
4. Scan the indices between the two global bounding boxes. Count zeros on the
   whole scanned line, including zeros outside the `9` bounding-box span.
5. When the count is at least the episode's threshold, recolor only original
   background `6` within the orthogonal span of the `9` bounding box to `2`.
   Preserve zeros and all other original cells.

`program(1)` returns the exact selected canonical source bytes. The two
alternative programs replace only the canonical row/column `for/or` trigger
expressions with an integer zero-count comparison. Both source sites must match
exactly; an authority change requires a new review.

## Episodes and demonstration identifiability

The seed chooses `min_zeros` once per episode, independently of scene draws.
An explicit setting can also be supplied. Three demonstrations and one query
share that setting. Every scene contains between-lines with zero counts
`0`, `1`, `2`, and `3`, with at least one original background connector cell left
on each informative line. Thus every input distinguishes the declared settings.
Exact executed rival outputs verify this property instead of assuming it.

Scene inputs vary dimensions, marker order, marker shape, trigger positions and
orientation. They include disconnected marker cells, unequal marker bounds,
zeros outside the connector span, preserved non-background cells, and horizontal
off-alignment. The same input constraints support all three threshold values;
the four count witnesses are teaching constraints, not a change to the rule.

Each accepted input must pass the selected generator's `self_check`. Every
label and every rival prediction comes from the included protected Racket
bridge using the existing source normalizer. No Python rule mirror supplies
labels. Four leave-one-out query rotations use the same executed pairs and
check both declared parameter rivals. A rival fitting all demonstrations and
disagreeing on the held-out query is reported as `ambiguous`; agreement on all
pairs is `survived_all`.

## Run

From the outer extraction directory:

```bash
python3 review.py run python3 generators/520fe6e64fb6/workspace/parametric/threshold.py --seed 17 --min-zeros all --out ../checks/parametric/threshold-s17
python3 review.py run python3 generators/520fe6e64fb6/tests/test_parametric_520fe6e64fb6.py -v
```

The payload runs from `WORK/repo`. Its output path is relative to that directory
and must not already exist. The equivalent wrapper from `WORK/` is
`python3 run_with_racket.py ...`. The included offline Racket installation, or a
compatible local `racket` on `PATH`, is required. The focused tests use only
standard-library `unittest` and the task's own runtime dependencies; they are
also discoverable by `pytest` in the official task-test stage.

`--min-zeros auto` selects the seed's fixed setting; `1`, `2`, or `3` chooses one
explicit setting. `all` emits a separate complete episode for each setting on
the same four scene inputs, enabling direct comparison. A fresh output directory
prevents overwriting previous evidence.

The command writes:

- `public/episode-<opaque-content-id>.json`: demonstration inputs/outputs and
  query inputs only, without hidden parameters, rule code, or query answers.
- `private/episode-<opaque-content-id>.json`: seed, fixed parameter, exact source,
  query answers, all executed rival labels, and each query rotation's checks.
- `programs/min-zeros-{1,2,3}.rkt`: exact materialized programs for every setting.
- `private/default-parity.json`: canonical expected-label checks and default
  parity on representative selected-generator inputs.
- `private/negative-control.json`: an intentionally uninformative training set
  with a discriminating query, retaining the resulting measured ambiguity.
- `receipt.json`: source/program/artifact hashes, command, runtime identity,
  counts, and finite-scope limitations.

## Limits

This prototype changes one bounded semantic threshold and preserves the object
roles and spatial rule. It does not add a production parametric interface.
Evidence covers the reported settings, seeds, examples and declared threshold
rivals. It does not establish general identifiability against every conceivable
rule. Leave-one-out query rotation is an episode-position check, not a claim
that the branch rule is invariant under arbitrary spatial rotations.

The teaching sampler intentionally enforces four informative zero-count lines;
it is narrower than all lawful canonical inputs. The default rule itself is
byte-identical to the canonical authority, whose behavior extends beyond those
teaching inputs. The negative control is expected to be ambiguous and is not
counted as a successful teaching episode.
