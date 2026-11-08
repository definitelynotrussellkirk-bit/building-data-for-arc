# Barrier capacity: proposed task-local prototype

This is a **proposed prototype** for `dc155169ea57` (original ARC task
`84ba50d3`). It does not select a new production rule, change catalog approval,
edit shared runtime interfaces, or admit examples to training. Canonical
repair evidence is separate from the tests and episodes described here.

## Parameter and preserved reasoning

| Parameter | Allowed integers | Original/default | Meaning |
| --- | --- | --- | --- |
| `barrier_capacity` | `1`, `2`, `3` | `1` | A connected shape passes through when every occupied row has at most this many cells. |

The object extraction remains maximal four-connected components of color `1`
above one full-width color-`2` row, on color-`8` background. For each component,
count its cells by row. If any row exceeds the capacity, move the whole shape
until its **lowest such row** is immediately above the barrier. A tail below
that supporting row may cross the line. If no row exceeds the capacity, move
the shape to the floor and punch color-`8` holes in every occupied column of the
line. Erase the original component cells. Apply all line holes after drawing
moved shapes, exactly as the canonical authority does.

The parameter changes the executed transformation, including the supporting
row of one object. It does not change the input palette or connected-component
semantics. The `witness.json` example has a width-3 upper row, a width-2 lower
row, and a thin tail: capacities 1, 2 and 3 respectively use the lower support,
the upper support, and the floor. The three Racket outputs are distinct.

At capacity 1, `materialize_rule()` returns the exact canonical program read
through `reviewer_support.canonical_path`. Its whitespace-normalized catalog
hash is `c0f1818b0fb2`; its exact UTF-8 SHA-256 is
`2def524a1836b8bbbbf304e452ba7cfadf72ac353419ed428326edfcc2b167e6`.
For capacities 2 and 3, the only edit is the literal in
`(> (row-count rr) 1)`. There is a one-site assertion and a canonical hash guard.

## Runnable four-query command

From the **outer extracted packet directory**, where `review.py` lives:

```bash
python3 review.py run python3 \
  generators/dc155169ea57/workspace/parametric/prototype.py \
  --seed 17 --capacity 1 --capacity 2 --capacity 3 \
  --demo-count 2 --query-count 4 \
  --out ../checks/parametric/episodes-s17
```

Choose a new output path on replay; the script refuses an existing directory.
The wrapper runs the payload from `WORK/repo` and selects the bundled offline
Racket. Without `--capacity`, the default is the original value 1. Repeated
`--capacity` flags request separate fixed-rule episodes using the same input
seed for controlled comparison. `--sample-capacity` instead selects one value
deterministically from the seed and fixes it across the entire episode.

`--demo-count` and `--query-count` are independent. Two through 64 demonstrations
and one through 64 queries are accepted; 64 is an authoring bound, not a claim
that every count and seed has been exercised. Too few demonstrations, invalid
counts or capacities, duplicate requested settings, ambiguity, and exhausted
unique-input attempts fail explicitly. No shorter episode is silently returned.

All emitted inputs obey the same canonical structural envelope, independent
of capacity: dimensions 7..30, one barrier with at least three rows on either
side, and all blue components above it. The prototype sampler uses a narrower
scene grammar with width-2/3 boundary objects, width-4 support rows, variable
tails and thin bars. It samples demonstration sizes 16..18 by 20..22. Its first
four query sizes are 20×24, 24×20, 30×30 and 23×28. Shape profiles, tails and
positions vary along with dimensions; these are new scene draws. A bounded
hash-based rejection loop forbids repeated inputs across either split.

## Label execution and identifiability

Every demonstration and query label is obtained by executing the materialized
program with the supported public `RacketBridge` context, `eval_text`, and
`define_grid` APIs. A local `rule!` procedure returns the lambda, allowing the
unchanged rule expression to be bound and invoked. No private runner helper is
imported. A Python mirror is a parity check; it never supplies exported labels.
The evidence command also executes all four labelled canonical pairs under the
original setting.

For each selected capacity, the prototype compares six exact Racket rivals:

- The two other allowed capacities.
- Stopping the lowest cell immediately above the line.
- Using the highest qualifying support row.
- Sending every shape to the floor.
- Leaving the line unpunched.

`fit_rivals` accepts only demonstration input/output pairs. The program runs
and rejects fitting rivals **before any query is sampled or labelled**. Each
query receives its own receipt referring to that same demonstration-only fit.
An empty or insufficient teaching set remains ambiguous rather than borrowing
query answers. These checks establish finite distinguishability against this
inventory; they do not prove identifiability against all possible rules.

## Evidence and public challenge boundary

Each setting writes three files with neutral episode numbering:

- `episode-NN-challenge.json`: exactly `train` input/output pairs and `test`
  input grids. It contains no parameters, seeds, programs, query answers or
  private metadata.
- `episode-NN-private.json`: hidden setting, query labels, source/rule hashes,
  accepted input hashes and dimensions, full rival programs/predictions,
  demonstration refutations, and per-query checks.
- `episode-NN-rule.rkt`: the exact program used for labels.

The directory also contains `witness.json` and `manifest.json`, with canonical
checks, runtime identity, executed-grid counts and content hashes. Supply only
the challenge file to a solver. The adjacent private/rule files are authoring
evidence. The command log and test receipts live under `WORK/checks/parametric`.

## Focused tests

From the outer packet directory, without pytest or additional Python packages:

```bash
python3 review.py run python3 -m unittest discover \
  -s generators/dc155169ea57/tests -p test_parametric.py -v
```

The tests cover hand-derived threshold/support/tail outputs, independent
components sharing columns, exact canonical authority and all four labelled
canonical pairs, invalid parameter/count rejection, all three settings with
four unique queries, public leakage, deterministic seed replay, independent
counts, and demonstration-only rival fitting. They are prototype tests, not
an approval or a replacement for the canonical generator's checks.
