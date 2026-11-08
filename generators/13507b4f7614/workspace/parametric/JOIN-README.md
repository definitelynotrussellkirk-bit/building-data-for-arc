# Join aligned rectangles, then infer their new center crosses

**Status:** opt-in native adapter; reviewer qualification is separate from owner
acceptance and from training admission. The production generator and canonical
Racket authority are unchanged. `join_axis=none` returns the exact selected
763-byte program stored in `canonical.rkt`.

## Episode rule

The private episode-fixed parameter is `join_axis`:

| Value | First operation | Second operation |
|---|---|---|
| `none` (canonical default) | Identity | Original center-cross rule |
| `horizontal` | Fill one blank column between equal-height, row-aligned solid yellow rectangles | Recompute components and run the original center-cross rule |
| `vertical` | Fill one blank row between equal-width, column-aligned solid yellow rectangles | Recompute components and run the original center-cross rule |

Bridge eligibility is calculated simultaneously from the original components.
Every bridge cell must be zero. Every qualifying original pair is considered,
including successive pairs in a chain and independent groups. The second
operation transforms only **solid rectangles with both dimensions odd**. All
other components remain as they are in the intermediate grid.

This is a real state dependency: joining changes component membership and
bounding-box dimensions. Two width-two pieces can become an odd width-five
rectangle that becomes a cross; three width-two pieces become even width eight
and remain solid. Applying reduction first, or reducing the original objects
without recomputing them, gives a different answer. The retained causal witness
executes the intermediate, the actual program, and a skip-A program in protected
Racket. Its identity is bound to the native qualification.

## Constructive teaching and input grammar

`adapter.generate(seed, settings, demos=3, queries=4)` supports exact integer
seeds `0..2**63-1`, independently **2–6 demos** and **1–4 queries**. The intended
training request is three demos and four queries. Invalid settings, extra keys,
booleans, floating counts, unsupported counts, and negative seeds fail closed.

Inputs use background 0 and solid cardinal color-4 rectangles. Two blank rows
and columns separate the four layout regions; one-cell internal gaps supply the
join candidates. Inputs vary rectangle dimensions, translations, parity,
orientation, object count, chain lengths, and boundary contact. The separate
parametric domain extends beyond the selected sampler's 2..7 rectangle dimensions
and at most three objects. It retains the same exact canonical transformation.

The first two demonstrations teach:

1. Two even-length pieces join into an odd rectangle, which is reduced.
2. Three even-length pieces join into an even rectangle, which is preserved;
   two independent groups in each orientation teach repeated application.

The second example occupies a 20×20 canvas so the three-piece groups fit without
reducing the demonstration count. Mixed-parity pieces also distinguish the
actual AND guard from height-only or width-only shortcuts. Additional demos
vary these structures. Queries include new positions/sizes, longer chains,
multiple independent groups, and parity combinations.

The minimum sampled canvas is 16×16. Four query sizes are 16×19, 20×24, 25×22,
and 30×30. The 30×30 query fills all four regions substantially and contacts all
four canvas edges; it is not a padded small scene. The input stream does not
use the setting, requested demo count, or requested query count. More demos or
queries extend fixed prefixes, and query inputs never reuse a demonstration.

The bounded self-review executes the three setting programs plus these nine
rivals: skip joining, reverse the order, ignore parity, join both axes, skip
reduction, check height only, check width only, join only the first pair, and
join only the first connected group. Surviving rivals may agree on the sampled
queries; such agreement is explicitly finite. No universal identifiability,
all-seed reliability, transfer benefit, or model performance is claimed.

## Reproduce from the packet root

Use the interpreter that passes `review.py python-check`. With the packet's
isolated environment:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/13507b4f7614/tests

WORK/.venv/bin/python review.py run python3 \
  generators/13507b4f7614/workspace/parametric/build_evidence.py \
  --out generators/13507b4f7614/workspace/parametric/evidence/new-run \
  --demos 3 --queries 4
```

The evidence builder uses seeds 0 and 17 for every setting and a single protected
Racket session. It executes every setting and finite rival on all sampled
inputs, checks claimed labels, and checks identifiability using demos alone.
It refuses existing output destinations and duplicate visible challenges;
`verify_bundle(path)` checks serialized hashes and public/private projection.
Serialization verification does not re-execute Racket.

The existing native path inventories sources and evidence, then qualifies:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest \
  13507b4f7614 \
  --evidence generators/13507b4f7614/workspace/parametric/evidence/new-run \
  --include generators/13507b4f7614/tests/test_parametric_rules.py \
  --include generators/13507b4f7614/tests/test_parametric_adapter.py \
  --include generators/13507b4f7614/tests/test_parametric_evidence.py \
  --reported-checks 'State only actual executed checks and limits'

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  13507b4f7614 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/13507b4f7614/new-qualification --summary
```

An existing native manifest requires its exact current SHA256 via `--replace`.
Do not edit inventoried source/evidence after qualifying. Owner acceptance
must replay exact integrated source after intake; these commands do not grant it.

## Public and private data

The `public/` files are the native dataset projections: demonstration inputs and
outputs plus query inputs, named solely by their exact visible-byte SHA256.
They contain no private setting, seed, reference program, query answer, or
setting-associated ordinal. These full four-query dataset files are owned by the
consumer/controller; do not pass a whole four-query file as a model turn.

For a model turn use `build_evidence.observation(private_episode, query_index)`.
It returns the same demonstrations and exactly one query input, without its
index, future inputs, total-count hints, labels, or final-turn hints. Query zero
has exactly the same content for one-query and four-query requests. The existing
consumer decides when the preceding answer permits revealing the next query.
No training loop or conversation controller is added here.

Programs, answers, settings, actual runtime identity, teaching checks, and source
records remain private. `rules.py`'s Python transform is a diagnostic claim;
retained label evidence and native qualification execute protected Racket.

## Known limits and current findings

This is a bounded, constructive four-region family, not arbitrary packing of
all lawful rectangle grids. All colors are fixed at 0/4; shape sizes/arrangements
carry the variation. The exact original sampler's previously retained scalar
validation audit remains open. Its same-parity-only sampling also fails to
teach the AND parity guard against height-only/width-only rivals; this new
parametric teaching grammar covers those cases without changing approved bytes.

The first pre-repair parametric sampler failed a one-bridge rival on a query by
31 cells despite two fitting demonstrations. The minimal executed witness is in
`WORK/checks/13507b4f7614/self-review-before.json`; the repaired first two demos
and the two new executed rivals prevent that observed hole in the checked runs.
