# Dependent row and column selection

This separate family extends `2ca60ab198d6` without changing its canonical
generator or reference. `selection` is fixed for an episode:

| Setting | Transformation |
|---|---|
| `rows` (default) | Select rows whose left guide is exactly 7, preserve their order, and remove that guide column. The reference text is byte-for-byte canonical. |
| `rows_then_columns` | Perform that row selection, use the first surviving payload row as a column guide, then remove that row and retain its exactly-7 columns from the other surviving rows. |

The alternate setting preserves the source task's selector interpretation,
ordered filtering, and cropping. Its additional dependency is **dynamic guide
binding**, not an iterative simulation: the first surviving row determines which
columns the second stage keeps. A wrong original-top-row guide can produce a
different result of the same size. The native causal witness records an actual
qualified input, intermediate, program, counterfactual, and executed outputs.

## Input and request contract

`adapter.program(settings)` returns exact Racket text.
`adapter.generate(seed, settings, demos=3, queries=4)` returns private `train`,
`test`, and `program_solution` with Python-claimed labels. Native qualification
independently executes every label using protected Racket. Do not treat an
unverified direct Python return as a labeled training sample.

- Settings name exactly `selection=rows|rows_then_columns`.
- Seed is an exact integer in 0..2^63-1; booleans and floats are rejected.
- Demo counts are independently selectable from 2 through 6, ordinarily 3.
- Query counts are independently selectable from 1 through 4, ordinarily 4.
- Inputs are 6..30 rows by 7..30 columns, with at least three selected rows,
  two rejected rows, and a selected header containing at least two orange
  columns, two rejected columns, and both zero/nonzero rejected cues.
- The sampler has separate fixed demo/query index ranges, uses local RNGs,
  and returns identical inputs across settings for the same request.
- Every payload row contains content and orange cues or decoys. The first two
  demonstrations expose nonzero rejected guides, irregular/adjacent selected
  rows, more than three selected rows, and different 2/4-column masks.
- Query profiles are 6x7, 13x17, 23x26, and 30x30. The largest contains 18
  selected rows and 15 selected columns, dense distributed content, and
  rejected rows/columns across the canvas. This extends the production
  generator's 6..10 by 7..11 size range only within this separate family.

`make_input` offers explicit dimensions, keep counts, column counts, and density
for future bounded probes. The episode sampler itself uses a small constructive
profile schedule, not unrestricted random shape/count sampling. It fails
visibly on a declared-rival ambiguity rather than silently returning a short
episode or changing the private setting.

## Demonstrations and reference evidence

The Python teaching screen fits eight row-mode rivals and nineteen nested-mode
rivals to demonstrations only, then tests any survivors against each query.
These include nonzero/any-orange/alternating/first-three row selection, wrong
raw or final headers, nonzero/union/span/first-or-last-k column selection,
reversed or sorted row order, retaining the column guide, and the other declared setting.
`audit.py` repeats the finite comparison with executed Racket programs and
validates labels, requests, large grids, and public projection. Runtime errors
do not count as successful rival refutation. This is finite evidence, not a
proof of uniqueness against arbitrary programs or of learning benefit.

From the outer packet directory, run the focused audit and export two example
episodes (choose a new output directory):

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/2ca60ab198d6/workspace/parametric/audit.py \
  --out ../checks/2ca60ab198d6/audit
```

The public four-query files are **controller containers**. A model turn uses
only demonstrations plus the current query input. A first-turn projection has
identical bytes for a one-query and four-query request; it contains no future
input, answer, hidden setting, seed, total-query count, or full-container ID.
Public file IDs hash only their exact visible bytes. Private labels, programs,
settings, and evidence are kept separately.

After the source and audit are final, build the native inventory and qualify:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest 2ca60ab198d6 \
  --evidence generators/2ca60ab198d6/workspace/parametric/evidence/current \
  --include generators/2ca60ab198d6/tests/test_parametric.py \
  --reported-checks 'See the retained focused audit and test receipt; finite sampled scope.'
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 2ca60ab198d6 \
  --out ../checks/2ca60ab198d6/qualification --summary
```

The owner must qualify and accept the exact integrated bytes. Reviewer
qualification is not live owner acceptance and does not admit training data.

## Resolved teaching finding

The initial seed-44 two-demo nested lesson allowed stable ascending sorting
of the final rows by their first cell: it fit both demonstrations but changed
three of four query answers. The original lesson and both executed Racket
interpretations are retained in `checks/2ca60ab198d6/sort-shortcut-before.json`
in the return packet as an explicitly underidentified, unadmitted example.
The sampler now makes an interior selected row exceed the final selected row
at the first output column, refuting both monotone orders constructively. The
demo count stays at two; explicit ascending/descending rivals and a failing-then-
passing seed-44 regression cover the repair.
