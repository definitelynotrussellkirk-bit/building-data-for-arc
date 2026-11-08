# Enclosed-area thresholds: native parametric family

This is a separate proposed family for `b28619e32f6f` (legacy `00dbd492`).
The approved production generator and its canonical Racket authority are unchanged.

| Private episode setting | Executed transformation |
|---|---|
| `{"threshold_mode":"fixed"}` (default) | Exact canonical source: enclosed zero areas <=8 become8, <=24 become4, otherwise3. |
| `{"threshold_mode":"relative_to_largest"}` | Find the largest enclosed zero area M across every frame; areas n with4n<=M become8, otherwise2n<=M become4, otherwise3. |

Both rules discover four-connected zero regions, preserve border-connected
exterior zero, and preserve red boundaries/dividers/decoys. Labels use exact
integer comparisons. The alternative's largest-area intermediate is input
dependent: changing a remote enclosure can change another enclosure's color.
This is contextual gating, not iterative state simulation.

## Run in the supplied packet

From the outer folder containing `review.py`, use the interpreter that passes
`review.py python-check` (the example uses the packet-local test environment):

```sh
WORK/.venv/bin/python review.py run python3 -m pytest generators/b28619e32f6f/tests/test_parametric.py -q
WORK/.venv/bin/python review.py run python3 generators/b28619e32f6f/workspace/parametric/verify.py --out ../checks/b28619e32f6f/selfaudit-new
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify b28619e32f6f --demos 3 --queries 4 --out ../checks/b28619e32f6f/qualification-new --summary
```

Use new output directories. The native manifest must be current before
qualification; see `docs/parametric-promotion.md` for its source inventory command.
After intake, the owner must qualify and accept the exact integrated sources.
Reviewer qualification is not owner acceptance or training admission.

## Counts, construction and teaching

`adapter.generate(seed, settings, demos=3, queries=4)` supports exact integer
seeds0..2**63-1, independently2–6 demos and1–4 queries. All inputs in an episode
are distinct. Invalid types, booleans, unknown settings and unsupported counts
raise `ValueError`. Input RNG streams do not depend on the hidden rule setting.

The first two demonstrations construct these enclosed-area sets:

- M32: 7,8,9,15,16,17,24,25,32.
- M51: 11,12,13,23,24,25,26,51.

They expose both fixed cutoffs and their neighbors, equality at both relative
cutoffs, and nonintegral cutoffs that defeat upward/nearest rounding. They have
several frames, notched or holed rooms, inflated bounding boxes, and a
diagonal-only contact between two zero regions. Frame positions, order, room
notches, rotations and reflections vary. Later demos/queries vary areas and
geometry. The four query profiles are7×7,17×20,24×30,30×30, with rotations.
The30×30 scene has two full-height frames, a border-connected exterior strip,
and multiple rooms spanning the canvas, including a96–120-cell region.

`verify.py` checks the first TWO demos against finite authored competitors,
even in six-demo episodes. It tests cell/bounding-box area, both bbox numerator
and denominator, four/eight connectivity, inclusive/strict cutoffs, fixed and
per-frame maxima, global totals, exterior inclusion, rounding and simple fills.
Five named rule variants also execute through protected Racket. All retained
true labels execute through the same protected runtime. The finite checks do
not prove uniqueness against arbitrary programs or every seed.

The previous even-M design admitted a ceiling-threshold shortcut. Its two
Racket-labeled demos, disagreeing query and both programs are retained in
`checks/b28619e32f6f/selfaudit-final/teaching-repair.private.json`; that query is now a
mandatory distinguishing demonstration. The production generator's inherited
8/24-boundary coverage audit remains unresolved; this separate prototype does
not claim to repair the production sampler.

## Public/private boundary

The verification writer retains four queries and answers in
`episodes.private.json`, with settings/programs/controller mappings private.
Its `public/` files contain only demonstrations and the first query input.
`turn_bytes(episode, query_index)` projects one currently requested query; use
it only when the controller reveals that turn. It emits no index, total-count,
future-query, answer, seed, setting or program fields. The first-turn bytes are
identical to a single-query request. Filenames are full SHA-256 hashes of the
exact public bytes, so private changes cannot alter their identity.

`prototype.py` is the shared implementation; the thin adapter loads it by exact
adjacent path. Native generation re-executes the Python label claims in Racket.
`canonical.rkt` preserves the original source byte-for-byte, and `relative.rkt`
is the alternative authority. No global runtime interface is changed.
