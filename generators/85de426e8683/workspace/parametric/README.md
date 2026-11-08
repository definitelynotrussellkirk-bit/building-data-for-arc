# Diagonal targets: count before choosing ink

This separate native adapter preserves the production generator and the exact
canonical Racket program. `ink_rule=fixed_yellow` is the canonical transformation.
`ink_rule=target_parity` first finds whole gray 8-connected diagonal triples,
counts those eligible objects, and paints their centers red (2) for odd counts
or yellow (4) for even counts. All other cells stay unchanged.

The dependency is nonlocal: adding a distant eligible object changes the center
color of an existing object with an unchanged local neighborhood. Counting gray
cells, every gray component, one diagonal slope, or local diagonal windows gives
different answers on the constructed witnesses.

## Run in an issued review packet

Run from the outer directory containing `review.py`, using the Python interpreter
that passed `review.py python-check` and `review.py setup`:

```sh
python3 review.py run python3 generators/85de426e8683/workspace/parametric/verify.py \
  --out ../checks/85de426e8683/new-example --seed 23 --demos 3 --queries 4

python3 review.py run python3 -m pytest -q \
  generators/85de426e8683/tests/test_parametric.py
```

Use a fresh output directory. `verify.py` runs real protected Racket, compares
the Python label claims, fits both native settings and twelve Racket shortcut
programs using demonstrations only, checks every query, and also checks the
adapter's 36 finite Python rivals. A surviving rival is harmful only when it
changes a query answer. A runtime error is a failure, never a refuted rival.

The tool rejects duplicate visible batches and publishes public files only after
all checks pass. Failed private findings remain available for repair. Reports bind
the exact task source, adapter/program/helper bytes and live Racket identity.

## Public and private outputs

- `public/` and `public.jsonl` contain the four-query **controller-side** challenge.
- `turns/` contains independent hash-named one-query challenges. Give the model
  one of these at a time, after the preceding answer. Each contains only the
  demonstrations and current input; no settings, seed, program, query answers,
  future inputs or total-query hint appears in the file or filename.
- `controller.private.json` supplies the ordered turn IDs to the controller.
- `private.jsonl` retains labels, settings, programs, rival outputs and coverage.
- `report.json` binds the files and records the finite verification scope.

The exact first-turn public bytes equal generating one query directly with the
same seed/settings/demo count. Challenge IDs hash only the serialized visible
bytes, using the shared `reviewer_support` projection. This tool builds examples,
not a training loop or turn controller.

## Supported grammar and teaching limits

Demo counts 2..6 and query counts 1..4 are independent; ordinary qualification
uses three demonstrations and four queries. Settings share exactly the same
input draws for a seed/count request. The rule is fixed throughout an episode.

The first demonstrations have 3, 4 and 9 true targets. The four-target example
uses a 1/3 slope split, an odd number of gray decoys with an odd total cell count,
and a non-gray diagonal triple colored 6 or 7. These features distinguish
single-slope counts, component/cell counts, local-window rules and color-blind
painting. Counts 3/4/9 also defeat monotone count thresholds while bracketing
ordinary query counts 3/5/7/8. With only two demonstrations, queries use counts
3 or 4: extrapolating outside that range would leave a threshold shortcut alive.
The first three demonstrations contain 6, 8 and 15 total foreground objects,
which also distinguish both all-object parity mappings. Two-demo queries keep
their total object count even, so a surviving all-object rule for fixed-yellow
remains query-equivalent. Extra demonstrations add counts 6, 3 and 4, never
exceeding six examples.

Inputs range from 12x18 to 30x30; every four-query request includes a full 30x30
case with 24 or 25 occupied object zones and content touching all four boundaries.
At least two eligible targets occupy opposite corners, so the global count
requires distant information. Long and branched gray near-misses, gray axis
triples and colored shapes occupy the other zones. These are substantive objects,
not empty padding. The minimum 12x18 lesson holds its six required objects.

This deliberately bounded grammar uses six-cell zones, fixed count/size teaching
profiles, a limited motif palette and zero background. It does not claim arbitrary
object layouts, exhaustive seed coverage, universal identifiability, or measured
learning benefit. The unchanged production sampler still uses its original
8..10 by 9..11 size range; large sizes belong only to this opt-in family. The
existing canonical color-blind-teaching audit is not cleared by this new sampler.

## Native handoff

`promotion.json` declares the API, settings and limits. The native manifest binds
the adapter, exact canonical resource, verifier, explicit tests and small scoped
receipts. Native qualification must run against that current manifest:

```sh
python3 review.py run python3 -m arcpuzzles parametric qualify 85de426e8683 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/85de426e8683/new-qualification --summary
```

The return includes source-bound qualification/execution and a protected-Racket
counterfactual dependency witness. Reviewer readiness is not owner acceptance.
After integration, the owner must qualify the exact live bytes and perform the
native acceptance replay. No training admission or mixture change is implied.
