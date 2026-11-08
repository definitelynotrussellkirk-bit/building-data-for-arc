# Frame or largest-region lattice anchor

This separate native parametric family preserves the approved production
generator. The episode-fixed parameter is `anchor`:

| Value | Transformation |
|---|---|
| `frame` (default) | Exact canonical program: four extreme regions become 2/4/1/8 in reading order, strict interior regions 7, other edge regions 0. |
| `largest` | Find the unique largest zero rectangle. Fill northwest/northeast/southwest/southeast regions relative to it with 2/4/1/8, the selected region with 7, and the other regions on its row or column with 0. |

Both rules preserve all full green dividers. The default Racket bytes have
SHA-256 `4b84d3d083f65dd1308ec1941060c395f565103bf41b79a9713164eadd8942e7`.
Python outputs are label claims. Native qualification independently executes
every demonstration and query through protected Racket.

## Admitted geometry and causal dependency

Inputs contain only 0 and 3, with three through six nonempty bands on each
axis, band widths 1..6, and one strictly widest band on each axis. Every green
cell belongs to a complete internal divider; adjacent or exterior dividers,
stray green cells and ties for largest are rejected. The largest region may
touch any outer boundary. This is a separate grammar and supports more lattice
topologies than the production generator's eight calibrated profiles.

The minimum is 6x6: `[1,2,1]` bands on both axes. The maximum is 30x30: six
bands summing to 25 on each axis. These are substantive complete lattices,
with regions and divider intersections spanning the canvas, not padding.

A identifies the largest rectangle and produces its matrix coordinate and
area. B classifies every other region relative to that coordinate. Moving the
largest region changes the later classification; fixing an incorrect pivot
changes the output. This is an input-derived reference controlling a subsequent
transformation, not an iterative simulation of an updated grid. Because lattice
area factors as row-height times column-width, separately finding the widest
row and column is an equivalent correct algorithm.

## Episode construction

`adapter.generate(seed, settings, demos=3, queries=4)` accepts exact integer
seeds 0..2**63-1, 2..6 demonstrations and 1..4 queries independently. The
default is three demonstrations and four distinct novel queries. Each input
stream is keyed by seed, role and index, independently of the setting or counts.
Increasing either count preserves existing pairs; changing the setting
preserves all inputs.

The first demonstration uses five-by-five regions with an off-diagonal,
noncentral interior pivot and witnesses all four relative quadrants. The second
uses four-by-four regions with a different boundary pivot, exposing a rule that
incorrectly searches only interior regions. Additional demonstration topologies
and all query topologies are distinct, so construction needs no rejection loop.
Query canvases are 6x6, 13x19, 24x27 and 30x30. Small queries can legitimately
have identical answers under both settings; demonstration labels identify the
episode rule before any query answer is consulted.

The second pivot is `(0,0)`, so the two demos also break an initially discovered
anti-diagonal shortcut that inferred the pivot column from the row and ignored
column widths. The source-bound failing example and regression are retained;
the repair keeps the two-demo minimum.

## Reproduce the bounded evidence

From the outer extracted packet directory, with its bundled Racket configured:

```bash
python3 review.py run python3 generators/9c5bdbcdcd50/tests/test_parametric.py
python3 review.py run python3 generators/9c5bdbcdcd50/workspace/parametric/probe.py check --out generators/9c5bdbcdcd50/workspace/parametric/evidence/current
python3 review.py run python3 -m arcpuzzles parametric manifest 9c5bdbcdcd50 --evidence generators/9c5bdbcdcd50/workspace/parametric/evidence/current --include generators/9c5bdbcdcd50/tests/test_parametric.py --reported-checks 'Use the actual retained check results and limits'
python3 review.py run python3 -m arcpuzzles parametric qualify 9c5bdbcdcd50 --out ../checks/9c5bdbcdcd50/qualification
```

Use a new output path after edits; the manifest helper requires the existing
manifest's exact `--replace` hash when deliberately refreshing it. The probe
also has a `witness` subcommand that binds its already executed causal cases
to the qualification. Run `probe.py witness --help` for its exact arguments.

The probe retains private four-query episodes and separately projects one
query per public challenge, using the existing public-byte serializer and
SHA-256 filenames. First-turn bytes match a one-query request exactly. Settings,
programs, query answers, future inputs and total-count hints remain private.
The downstream controller owns conversation turns; this family adds no trainer
or controller. Finite-rival checks establish only the tested distinctions.

Owner qualification and fresh exact-source acceptance remain separate steps.
After acceptance, four-query generation uses the existing API:

```bash
python3 review.py run python3 -m arcpuzzles parametric export 9c5bdbcdcd50 --count 4 --seed 12 --demos 3 --queries 4 --out var/datasets/lattice-anchors
```

No prototype evidence or qualification grants training admission.
