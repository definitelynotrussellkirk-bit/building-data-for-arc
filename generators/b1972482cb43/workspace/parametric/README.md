# Point reflection and visible-span echo

This is an opt-in native parametric family. The production generator and its
selected canonical Racket authority are unchanged. `rule=point` returns that
authority's exact 476-byte program. `rule=visible_span_echo` adds a second copy:

1. Reflect the source through the unique 9-anchor and clip individual cells.
2. Measure the **visible** first copy's bounding-box height and width.
3. If height is at least width, reflect that visible copy across the anchor's
   row; otherwise reflect it across the anchor's column. Keep the input and
   first copy too. Equal spans choose the row.

The intermediate is the clipped cell set, its two spans, and the selected axis.
Its content changes both the axis and which cells can be echoed. Measuring the
source instead, or echoing clipped-away cells, gives different answers on the
constructive teaching examples. The protected causal witness is retained with
the review's native qualification, not supplied to model inputs.

## Grammar and counts

One 4-connected monochromatic shape of 2–240 cells, one color-9 anchor, background
zero, exact integer colors, and grids 4–30 rows by 5–30 columns. The first
reflected shape must be disjoint from its source and have at least one visible
cell. This deliberately extends only the opt-in family's shape/size domain;
the canonical sampler's 2–5-cell, 4–12 by 5–14 domain is unchanged. Both settings
are total on the extended grammar and use identical sampled inputs.
The validator's 2–240-cell range is broader than the current constructors:
sampled shapes have 3–169 cells. No claim is made that every admitted topology
or cell count is sampled.

The adapter supports **3–6 demonstrations** and **1–4 queries independently**.
Three demonstrations teach a clipped plus, a complete tied-span L, and a clipped
tall L. Odd block scaling and flips preserve those geometric distinctions; a
finite-rival guard checks the actual result. One demonstration uses a larger
connected shape. Additional demonstrations vary shape, color and canvas size.
Input selection never reads the chosen private setting.

Four queries have sizes 4×5, 18×24, 22×26 and 30×30. The last two contain larger
connected shapes with variable holes and rib patterns, spread across the canvas
by the reflections. They are substantive geometry tests, not padded tiny inputs.
The generator uses separate input/query random streams and returns fresh grids.
Its small constructor has at most 16 teaching attempts and a checked constructive
fallback; it never silently drops a requested example.

## Run in the supplied packet

From the outer folder containing `review.py`, with the prepared interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/b1972482cb43/tests/test_parametric.py

WORK/.venv/bin/python review.py run python3 \
  generators/b1972482cb43/workspace/parametric/probe.py \
  --out ../checks/b1972482cb43/replay --seeds 0 17 --demos 3

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  b1972482cb43 --out ../checks/b1972482cb43/qualification-new --summary
```

`probe.py` is the reusable authoring/audit tool. It rederives every label through
protected Racket, executes the finite rivals, retains demo-only teaching checks,
and writes separate public challenges and private evidence. Use a new output
directory each time. A source/evidence inventory must be current before native
qualification; see the repository's `docs/parametric-promotion.md`.

The public container has all four controller-side query inputs. Reveal only one
input per turn. The first-turn projection is identical to a one-query request;
it contains no setting, program, answer, future input or total-count marker.
Public IDs hash only exact visible challenge bytes. Query answers, source/runtime
identities, parameters and reference programs remain in private evidence.

## Evidence and limits

The task-local `evidence/manifest.json` binds the source and the declared audit
evidence. `WORK/checks/b1972482cb43/qualification/` holds native qualification and
execution evidence. `WORK/checks/b1972482cb43/causal/` holds the protected replay
of the wrong-intermediate counterfactual. `WORK/RESULTS.json` records actual runs,
failures repaired and the owner handoff.

The point rule has 12 declared rivals; the echo rule has 20. These cover the
alternative setting, fixed/grid-center anchors, whole-copy clipping, outline
copying, one-sided sources, axis reflections, translation, dropped input,
wrong colors, source-span selection, un-clipped echoes, fixed/opposite axes,
tie direction, echoing the source and dropping the first copy. Passing this
finite set is not universal uniqueness or a measured learning benefit.

Reviewer qualification is **ready for owner intake**, not native acceptance.
The owner must integrate and qualify/accept the exact live source. Nothing here
admits data to training or changes the production data mixture.
