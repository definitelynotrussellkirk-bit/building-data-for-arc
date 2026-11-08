# Object-count histogram variants

This is a separate native parametric adapter for `c2cd365ed4fa` (`aaecdb9a`).
The production generator and the canonical reference remain unchanged.

## Rule and dependency

Both settings segment each of the colors **5, 2, 8, 9, 6** into monochromatic
8-connected components on background 7. Each component contributes one unit to
its color's bar, regardless of area. Bars are bottom-aligned in five columns.

- `column_order: fixed` returns the exact canonical program bytes, with columns
  in the order 5, 2, 8, 9, 6.
- `column_order: count_ascending` computes the component-count vector, then uses
  that input-dependent vector to select the column permutation. Equal counts
  retain the base order 5, 2, 8, 9, 6. Absent colors retain empty columns and sort
  before present colors.

The extension's causal dependency is **segmentation → count vector → column
selection → bar placement**. In the retained counterfactual, only the counts
used to select columns are changed to four-connected counts; bar heights still
use correct eight-connected counts. Different output positions therefore expose
the routing dependency, rather than only a change in histogram height.

## Supported sampler

`generate(seed, settings, demos=3, queries=4)` accepts exact integer seeds in
`0..2**63-1`, demonstration counts **2–6**, and independent query counts **1–8**.
Ordinary use is three demonstrations and four queries. Every input in an episode
is distinct. Repeating a request is deterministic, and the same seed/counts use
identical inputs under both settings.

The first two demonstrations are selected from bounded, constructive scenes.
They show diagonal connectivity, varied component sizes, a count of six,
nonuniform counts, positive ties, and a missing column. Selection consults only
the demonstrations and a finite declared set of rivals under both settings.
It does not inspect query labels or depend on query count. This repairs the
retained lesson-assembly failure in which three demonstrations without a
diagonal join allowed four-connectivity to survive until the query.

Inputs are irregularly placed objects, with same-color objects separated in all
eight directions. Different colors may touch. Object sizes are not determined
by their color's component count. The first four objects touch different canvas
edges. Counts remain at most six and components at most sixteen cells. The
canonical generator's admitted canvas is 10–22 per axis; this separate adapter
uses 10–30. Its four query profiles include 10×10, 30×30, 10×30, and 30×10.
The 30×30 profile has at least 150 foreground cells across all four boundaries.
The grid is not enlarged by padding a small central puzzle.

Each scene has at most 64 placement attempts; demonstration construction has at
most 48 candidate pairs. Exhaustion raises an error, never a short episode.
The grammar and evidence are bounded; no universal solvability or learning-gain
claim is made.

## Commands

From the outer packet directory after `review.py setup`, use its passing Python
interpreter (replace `python3` with `WORK/.venv/bin/python` when using the venv):

```bash
python3 review.py run python3 -m pytest generators/c2cd365ed4fa/tests/test_parametric.py -q
python3 review.py run python3 generators/c2cd365ed4fa/workspace/parametric/prototype.py --seed 17 --demos 3 --queries 4 --out ../checks/c2cd365ed4fa/examples-new
python3 WORK/check_public_exports.py WORK/checks/c2cd365ed4fa/examples-new/public --demos 3 --queries 4
python3 review.py run python3 generators/c2cd365ed4fa/workspace/parametric/verify.py --out ../checks/c2cd365ed4fa/focused-new
```

All output paths must be new. The exporter executes every claimed label through
the live protected Racket runtime before writing. `public/` contains only
demonstration pairs and query inputs; filenames are the SHA-256 of the exact
visible bytes. `private/` retains settings, programs, seeds, answers, and finite
teaching evidence. Batch IDs are sorted, and duplicate visible payloads fail.

The multi-query file belongs to the controller. Pass
`prototype.turn_bytes(episode, query_index)` to the model for the current turn:
it contains only the demonstrations and that one query, with no total-count or
future-input hint. The first turn is byte-identical for one-query and four-query
requests with the same seed, setting, and demonstration count. No training loop
or conversation controller is introduced here.

## Qualification and owner handoff

`promotion.json` declares both settings and the request limits. The task-owned
`evidence/manifest.json` binds the current adapter, sources, canonical resource,
tests, and focused evidence. Native qualification and execution receipts are in
`WORK/checks/c2cd365ed4fa/qualification/`; the protected causal witness is in
`WORK/checks/c2cd365ed4fa/causal/` in the returned packet.

After integrating the patch, the owner must qualify and accept those exact live
bytes using the repository's native `arcpuzzles parametric` commands. Reviewer
qualification is not native owner acceptance, and neither grants training
admission. The checks cover the declared settings, named rivals, and retained
seeds, rather than every possible rule or future draw.
