# Complete gaps, then recognize frames

This opt-in proposal keeps production `generator.py` and the selected canonical
authority unchanged. The default `{"completion":"none"}` returns the exact
selected program in `canonical.rkt`. The alternative
`{"completion":"single_gap"}` executes `single_gap.rkt`.

## Rule and domain

On the original grid, find the four-connected components of orange (7). For each
component whose bounding box has both dimensions at least three, compare its
cells with that box's perimeter. If it equals the perimeter minus exactly one
cell, and that missing cell is zero, add orange at that cell. Perform all such
repairs simultaneously once. Recompute orange components on the resulting grid.
For every component exactly equal to its bounding-box perimeter, paint only its
zero interior cells cyan (8). Preserve all other cells.

Non-orange interior cells, including existing cyan, are preserved. Orange objects
inside a frame are independently detected. Repairs can join separate orange
components: the merged component must be recognized anew and may fail the exact
frame test. `first_stage` returns that repaired grid; `analyze` additionally
reports added cells, recognized boxes, and the claimed final output.

The admitted input domain is every rectangular exact-list grid of exact integer
colors 0..9 with each axis 3..30. This domain is broader than the unchanged
production sampler's frame-only grammar. Degenerate orange points and strips,
colored interiors, touching objects, nonframes and no-op scenes are lawful.
The Python functions are claim models, not protected reference execution.

## Episode API

`program(settings)` and `generate(seed, settings, demos=3, queries=4)` use the
same strictly validated, episode-fixed setting. Seeds are exact integers in
0..2**63-1; supported independent counts are 3..6 demonstrations and 1..4 queries.
The three constructive demonstrations are an isolated exact 3x5 frame, an
isolated 3x3 corner-gap frame, and a 27x27 scene with sixteen contrasting motifs.
The first two use larger canvases so minimum-size queries remain novel. The
crowded scene includes all four side-gap orientations under one common spatial
transform, exact 3x3 and larger frames, colored interiors, non-orange decoys,
two-gap shapes, a tailed shape, a diagonal contact, an occupied gap and a repair
that merges orange objects. One side-gap frame is 3x6, teaching both minimum
thickness and extrapolation beyond five-cell frames. Optional demonstrations
keep the ordinary teaching prefix. The query bank contains minimum-size, rectangular,
larger and substantive 30x30 scenes, shuffled in full before prefix selection.
Seed streams and input draws do not depend on the setting or requested counts.
All returned grids are independent lists; all inputs within an episode differ.

The sampler uses separated motif slots and global reflections/transposition.
This is a finite structural distribution within the broad lawful domain, not a
claim to sample all possible overlapping or nested arrangements uniformly.
Independent hand cases and rival checks cover additional lawful structures.

An initial sampler used three independently transformed crowded scenes. Its
demonstrations sometimes supported square-only or one-orientation shortcuts,
and always supported an arbitrary minimum-two-orange-components context gate.
The current anchors and shared multi-motif scene repair those teaching holes
without adding demonstrations or changing any query input or answer. The
frozen independent 39-hypothesis bank and separate count-gate regressions live
in `../../tests/`; finite passes do not prove universal uniqueness.

## Native commands

From the packet's outer directory, using its Python 3.12 environment and bundled
Racket setup:

```sh
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify af6e765bcc41 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/af6e765bcc41/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/af6e765bcc41/qualification/qualification.json --out ../checks/af6e765bcc41/preview
WORK/.venv/bin/python review.py task-tests af6e765bcc41 --phase after --out ../checks/af6e765bcc41/task-tests
```

Choose new destinations for reruns. Qualification independently executes the
programs and all labels and fits declared settings using demonstrations only.
The preview contains one public current query per file. The bundle, listing,
permutation, source settings, programs and answers remain controller-private.
Neither qualification nor preview grants owner acceptance or training admission.
