# Fill all groups or the largest final bounding boxes

This is a separate parametric extension of `5d9c166a8c3b`. The selected
production generator and canonical reference are unchanged.

| Episode-fixed `fill_scope` | Executed transformation |
| --- | --- |
| `all` (default) | Exact canonical program: repeatedly merge groups whose current bounding boxes overlap in either row or column span, then fill zeros in every final bounding box red. |
| `largest_bbox` | Compute the same full closure, select every final group tied for maximum bounding-box area, then fill zeros only in those boxes red. Original foreground is preserved. |

The default program is the exact 2,938-byte selected reference, SHA-256
`7797859d093b1fd927ee3a81ad36d8216a775477d8709d77b38629450ff7f79b`.
Area includes the entire box, not just foreground cells. Ties select all maximal
boxes. Each setting is total over the admitted single-color input grammar.

## What makes the intermediate necessary

A merges the current object groups to a fixed point. Its input-dependent result
is a set of final memberships and recomputed bounding boxes. B compares their
areas and chooses which regions to fill. A new overlap created by an earlier
merge can change the largest group, so selection cannot be performed using the
original objects or the initial overlap graph.

The retained small 8x10 witness selects a 20-cell final bbox and adds 17 red
cells. A static-initial-graph counterfactual instead selects a different 8-cell
bbox and adds 3 red cells. The 30x30 witness occupies all four boundaries with
101 foreground cells; correct and counterfactual selections add 135 and 115
red cells respectively. `audit.py` executes both programs before retaining
these claims. Final source binding is attached in the return's sequential witness.

## Sampling and teaching

`adapter.generate(seed, settings, demos, queries)` supports exact nonnegative
integer seeds, 2–6 demonstrations, and 1–4 queries. Ordinary use is 3 demos and
4 queries. `prototype.generate` additionally accepts independent `height` and
`width` overrides, each 7–30. Calls outside the supported ranges fail visibly.

Two separated regions both gain filled cells: a three-object dynamic bridge
and a connected L-shaped object with a nontrivial bounding box. The bridge
wins in the first demo; the second has tied boxes; the third, when requested,
makes the connected region larger. A 7x7 canvas cannot fit the latter reversal,
so that requested shape profile is explicitly recorded as a tie. This is a
sampling limit, not a change of transformation.

The first demonstration requires a component skipped early in a scan to be
revisited after another merge. This repairs a demonstrated shortcut where one
merge scan fit all old demonstrations but changed a query. The second demo is
transposed, exposing an overlap created in the other axis. Queries vary scale,
reflection, transpose, foreground color, shape thickness, and relative area.
The first query is 30x30 in ordinary use; another is 21–29 in both dimensions.
Large inputs contain substantial objects and fill across the canvas.

The sampler is independent of the setting and total requested query count.
All pairs are distinct; duplicate draws have a bounded 64-attempt limit.
The Python claims are checked against twelve explicit wrong rules, including
one-pass and static-graph closure, row-only/column-only grouping, direct pairs,
original components, global boxes, foreground-count selection, smallest boxes,
one tie winner, outlines, and the other setting. Only demonstrations fit a
rival; queries determine whether a surviving rival would cause ambiguity.
This is a finite check, not proof against every possible alternative program.

## One reproducible authoring command

From the outer packet directory, using the interpreter that passes
`review.py python-check`:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/5d9c166a8c3b/workspace/parametric/audit.py \
  --seed 41 --out ../checks/5d9c166a8c3b/audit
```

Choose a new output directory for another run. This command executes saved
labels and declared-rival checks in protected Racket, verifies the two causal
witnesses, checks size boundaries and export privacy, and writes compact
source-bound evidence. Python mirrors alone never certify saved labels.

The `public/` directory contains four-query authoring projections; it is not
the first-turn model input. The `first_turn/` directory contains only the
demonstrations and first query. Controller-side private files retain all four
answers and future inputs. Both public formats use the SHA-256 of exactly
their visible serialized bytes as the filename. Settings, seeds, reference
programs, answers, and future inputs cannot affect a first-turn identifier.

The one-query call and first turn of the four-query call are identical.
Later queries belong to the existing controller's sequential reveal; this
extension adds no controller or training loop.

## Qualification and owner handoff

Run the focused tests, then inventory the exact sources and small task-local
audit evidence with the existing native manifest helper:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/5d9c166a8c3b/tests/test_parameters.py
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest \
  5d9c166a8c3b \
  --evidence generators/5d9c166a8c3b/workspace/parametric/evidence/current \
  --include generators/5d9c166a8c3b/tests/test_parameters.py \
  --include generators/5d9c166a8c3b/workspace/parametric/README.md \
  --reported-checks 'Use the actual checks and bounded coverage from this run'
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  5d9c166a8c3b --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/5d9c166a8c3b/qualification --summary
```

An existing inventory needs its exact current hash supplied with `--replace`.
The return includes reviewer qualification and execution evidence. The owner
must integrate the source, requalify the exact live bytes, and run fresh native
acceptance. No accepted record or training admission is created by this authoring
tool. The evaluation-task inspiration `195c6913` remains explicitly unverified
as a lineage relationship; only its geometry-dependent composition idea is used.
