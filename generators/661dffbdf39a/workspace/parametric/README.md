# Strict gray-density threshold prototype

This opt-in extension of `661dffbdf39a` keeps the noisy-separator reasoning:
detect gray-dense rows and columns, complete their lines, remove off-line noise,
and color each crossing with the input's unique non-black/non-gray marker.
One threshold is fixed for every demonstration and query in an episode.

| Parameter value | A line is detected when | Status |
| --- | --- | --- |
| `1/3` | More than one-third of its cells are gray | Proposed variant |
| `1/2` | More than half of its cells are gray | Exact canonical Racket text |
| `2/3` | More than two-thirds of its cells are gray | Proposed variant |

Comparisons are strict. On an 18-cell row, 6, 9, and 12 gray cells are exact
boundaries; equality does not select the row for its corresponding threshold.
Racket uses exact rationals for the variants. The default retains the original
`count > quotient(length, 2)` expression, which is equivalent to a strict
majority on both even and odd axis lengths.

## Generate three complete episodes

From the outer packet directory:

```sh
python3 review.py setup
python3 review.py run python3 generators/661dffbdf39a/workspace/parametric/export_challenges.py --out ../checks/threshold-examples --seed 1729 --train-count 3 --query-count 4
```

This creates one episode per threshold, each with three demonstrations and four
queries. Select one setting with `--threshold 2/3`. Demonstration and query
counts are independent: supported ranges are 1–12 and 1–16 respectively. Every
input within an episode is distinct. The writer refuses a nonempty destination
and rejects duplicate visible challenges before writing any batch files.

The three settings use the same input sequence for a given seed and count
configuration. Only their rule-dependent outputs change. This makes the
parameter comparison controlled and prevents the sampler from encoding the
threshold in dimensions, marker choice, or input positions.

The retained, executed examples are in `evidence/examples/`. To verify those:

```sh
python3 review.py run python3 generators/661dffbdf39a/workspace/parametric/export_challenges.py --verify generators/661dffbdf39a/workspace/parametric/evidence/examples --replay
```

In an ordinary checkout, use the same payload commands from the repository root
with `shared/runtime` on `PYTHONPATH` and a working `RACKET_PATH`. The packet
wrapper supplies both automatically. No pytest dependency is needed.

## Public and private export contract

Give a solver only `public/` and `index.json`. Each challenge contains exactly
demonstration inputs/outputs and query inputs. Its filename is the full SHA-256
of the exact bytes returned by `reviewer_support.public_challenge_bytes`; the
index is sorted by those public IDs. Private settings, seeds, query answers,
programs, and export order cannot affect these public names.

`private/` contains complete labeled episodes, their parameter mapping, exact
Racket programs, and source hashes. Keep this directory with the controller.
The manifest binds the prototype, exporter, public-projection helper, unchanged
canonical generator, and original canonical Racket text.

`--verify DIR` checks schemas, exact public bytes and filenames, sorted IDs,
file inventories, all retained hashes, and disjoint demonstration/query inputs.
It does not establish semantic correctness. Adding `--replay` also requires the
current source hashes to match, checks that each program is the current program
for its declared threshold, and executes every stored label in Racket. It never
substitutes a Python answer when Racket fails.

## Teaching domain and limits

The sampler uses 18- or 24-cell axes, two or three strong rows and columns,
and three partial candidates on each axis at the exact one-third, one-half,
and two-thirds boundaries. Randomized placements, marker colors, dimensions,
and noise provide variation. Strong lines have holes, so line completion is
required even at the strictest threshold. Ordinary lines never exceed the
lowest threshold. Consecutive samples vary strong-line counts; three standard
demonstrations therefore exercise changing row and column counts.

For every episode, Racket labels the selected rule and executes the other two
strict thresholds plus the selected threshold's inclusive `>=` rival on
demonstration inputs only. Each rejected rival retains its demonstration
witnesses. The same surviving rule governs all four default queries; query
answers do not participate in identification. One demonstration suffices for
this declared finite family. This is not a uniqueness proof over arbitrary
programs, and the sampler does not cover every possible ARC input geometry.

The default canonical generator, canonical ledger, catalog approval, and
production generation API are unchanged. The extension remains a proposed
prototype. Neither the evidence manifest nor exporting examples approves
the variants or admits trajectories to training.

## Focused regressions

```sh
python3 review.py run python3 -m unittest discover -s generators/661dffbdf39a/tests -p 'test_threshold*.py' -v
```

The new tests cover exact boundaries and transposes, original-pair and new-input
canonical equivalence, an odd rectangular majority case, independent counts,
determinism, validation, visible-only IDs, duplicate rejection, existing-output
protection, corruption detection, and Racket replay. Existing production test
fixtures and unrelated batteries are outside this prototype change.
