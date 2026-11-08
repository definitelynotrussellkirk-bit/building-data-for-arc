# Native marker-order family

This proposed family retains the canonical spatial reasoning and varies one
episode-fixed rule:

| `marker_order` | Meaning |
| --- | --- |
| `near_to_far` | Canonical/default: stable increasing minimum edge distance |
| `far_to_near` | Stable decreasing minimum edge distance |

Both infer the unique nonzero modal background, treat every other cell (including
zero) as a separate marker, retain row-major ordering inside distance ties, and
assign the ordered colors to output rings from outside inward. Unfilled inner
rings retain the background. Repeated colors remain separate markers.

`adapter.py` is the native entry point. Its default program is byte-identical to
the selected canonical Racket authority. The alternative changes only the sort
key. The older two-demo/one-query standalone authoring API remains available in
`prototype.py`; the native API and protected evidence below supersede that small
example as the qualification candidate.

## Counts, grammar and construction

`generate(seed, settings, demos=3, queries=4)` independently supports **2–6
demonstrations and 1–4 queries**, with four queries for training/qualification.
Seeds are literal integers in `0..2**63-1`; counts reject booleans and coercions.
Inputs are matched across settings. Separate demonstration and query streams
keep the query prefix unchanged when requesting more demonstrations or queries.
No rejection loop or silent count truncation is used.

The semantic domain is rectangular 5–30-cell sides, a unique nonzero modal
background, and at most one marker per available output-ring rank. Every marker
may occupy any cell; equal distances, repeated colors and zero are lawful. The
current constructive sampler covers the explicit shapes below, not every size
or every lawful marker placement.

The first two demonstrations construct the teaching evidence: an 11×13 scene
combines tied distances, a distance gap, a zero marker, repeated colors and an
unfilled center; a 29×30 scene uses all 15 output ranks and the opposite
numeric tie orientation. This rejects both increasing- and decreasing-color
tie-break shortcuts using only two demonstrations. Optional demonstrations
add four intermediate rectangular sizes. Four queries cover 5×5, 17×25, 23×29
and 30×30 (some rectangles transpose). The 30×30 case contains 15 spatially
distributed markers through edge distance 14, and paints every ring. This is a
separate sampler extension, not a change to production's more restrictive
profile validator. Every non-background cell has a role under this rule, so
unlabelled foreground distractors would change the task rather than add noise.

## Why the intermediate matters

**A:** stably rank all marker identities by their edge distance.
**Intermediate:** an ordered list of coordinates, distances and colors.
**B:** choose each output ring's color by its position in that list.

A marker relocation can change the ranks and output rings of several *other*
markers. A fixed per-cell recoloring cannot implement this dependency. The
retained paired witness moves one marker while preserving the row-major color
sequence, so a skip-sort program stays unchanged while the qualified program
changes. This establishes a nonlocal data dependency; it does not claim an
iterative simulation or prove a minimum amount of model reasoning.

## Reproduce bounded evidence

From the outer packet folder, using the interpreter that passed `python-check`:

```bash
python3 review.py run python3 \
  generators/1034300a135f/workspace/parametric/native_probe.py \
  --seed 19 --demos 3 --queries 4 --out ../checks/1034300a135f/native

python3 review.py run python3 -m pytest -q \
  generators/1034300a135f/tests/test_native_marker_order.py

python3 review.py run python3 -m arcpuzzles parametric qualify 1034300a135f \
  --out ../checks/1034300a135f/qualification --summary
```

The probe executes both settings and its declared shortcut programs through
protected Racket. It fits rivals to demonstrations only, checks surviving
predictions on each query, and refuses harmful survivors or execution errors.
The finite rival list is documented by the executable probe; it is not a claim
of universal uniqueness. The native manifest binds current source and compact
evidence before qualification.

## Public and private data

The export's `public/` files contain demonstrations and masked query inputs;
their exact bytes and filenames use the shared public-content hashing helper.
They are a controller-side evaluation bundle, **not a multi-query user turn**.
Use `native_public_turn(episode, query_index)` to expose exactly one query at a
time with the same demonstrations, without a total-count or future-input hint.
The first turn is identical for a one-query or four-query request. The caller
controls when to advance after receiving the preceding answer; this stateless
projection does not implement an interaction controller.

Private settings, programs, seed, answers and source/runtime evidence remain
outside those files. Changing private fields cannot change a public identifier.
Source inventory and native qualification are review evidence. Exact-source
acceptance after owner integration remains required; training admission remains
false.
