# Proposed endpoint/trace rule prototype

This task-local prototype belongs to `33f9169a335e`. It is **proposed** and
has no parametric approval or training admission. The selected production
`generator.py`, canonical record, and approval hashes remain authoritative.

## Rule and invariant reasoning

The bounded parameter is `mode` with values `endpoint` (default, canonical)
and `trace`. Both detect each positional inverted U in the original input:
a three-cell nonzero cap, two nonzero cells immediately below its ends, and
a zero cell below its center. The five foreground cells need not share a
color. Repeated object colors and mixed-color witnesses remain valid.

- `endpoint` places marker **4** in the bottom cell of each gap column. Its
  Racket source is the exact canonical ledger `program_solution`, stripped
  only of outer whitespace.
- `trace` places marker **4** in every originally empty cell from each gap
  row through the bottom in that column. It preserves all nonzero cells and
  continues below them. Witness detection reads only the original input.

Dimensions, witness detection, zero background, and output marker color do
not depend on mode. Inputs retain the selected generator's domain: 5..30 rows
and columns, no input 4, an initially empty bottom row, distinct gap columns,
and every foreground cell belonging to a detected U. Sampling calls the exact
selected production generator through `reviewer_support.load_selected_generator`
with a root anchored to this file, and rejects any nonempty `self_check` result.
Focused tests include a lawful mixed-color case with one ray crossing another U.

Every lawful input distinguishes these two modes: a U gap is empty and lies
strictly above the bottom row because its nonzero legs cannot lie in the
initially empty bottom row. Trace fills that gap; endpoint leaves it empty.
This establishes identifiability against the declared two-mode family. It does
not establish uniqueness against arbitrary rules or expand the production
sampler's monochrome-per-U support.

## API and reproducible four-query evidence

`ray_mode.py` exports `MODES`, `canonical_program()`, `rule_source(mode)`,
`python_transform(grid, mode)`, and
`sample_episode(seed, *, mode="endpoint", input_seed=None, demo_count=2,
query_count=4)`. An explicit mode is fixed for all demonstrations and queries.
Only `mode=None` chooses a mode using a local RNG seeded by `seed`. The default
`input_seed` is `seed`; supplying the same `input_seed` across modes produces
the same inputs in the same order, independent of the mode seed.

Both counts must be exact integers in 1..8; booleans are rejected. Seeds must
be exact integers, with signed values accepted. Sampling requires pairwise
unique inputs across demonstrations and queries and allows at most
`64 * (demo_count + query_count)` deterministic draws. Duplicates, rejected
inputs, and production `RuntimeError` draws consume that bound; exhaustion
raises with the requested count, accepted count, and last rejection reason.
Other programming errors propagate. No short episode is returned.

The API's outputs are Python expectations for authoring, not authoritative
labels. The separate retention writer executes the materialized rule through
protected Racket, checks those expectations, and retains executed labels,
source hashes, and demonstration-only rival checks. Run from the outer packet
extraction directory:

```bash
python3 review.py run python3 generators/33f9169a335e/workspace/parametric/retain.py --out ../checks/parametric/run-v1 --seed 20261023 --demos 2 --queries 4
```

This shared writer retains both U modes and the separately named public-task
analogy proposal. Public challenges contain visible demonstrations and query
inputs only. Hidden modes, seeds, reference programs, and query answers belong
to private evidence; opaque public identities depend only on visible content.
The writer's execution receipt records what actually ran and any limitations.

Focused prototype regressions (independent of canonical repair coverage):

```bash
python3 review.py run python3 -m unittest discover -s generators/33f9169a335e/tests -p test_parametric_ray_mode.py -v
```
