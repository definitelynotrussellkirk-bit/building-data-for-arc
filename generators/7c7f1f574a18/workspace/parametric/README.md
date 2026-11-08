# Enclosed-region area and horizontal docking

This native candidate extends `7c7f1f574a18` with the episode-fixed parameter
`min_hole_area ∈ {1, 2, 3}`. Setting **1 returns the exact canonical Racket
source**, including its formatting. The production generator and canonical
authority retain their existing behavior.

For each same-color, four-connected foreground component:

1. Partition the component's bounding-box complement into four-connected gap
   regions. Gaps contain every coordinate outside this component, regardless
   of that coordinate's color.
2. Discard regions touching the bounding-box boundary, then find the largest
   remaining region's area.
3. If the component fills its bbox, or that largest area reaches the episode
   threshold, preserve its rows and shape, recolor it 2, and dock it left.
   Otherwise recolor it 3 and dock it right.

The gap partition is an input-dependent intermediate. Multiple singleton holes
and one larger hole can have the same total missing area, bbox, color and
foreground cell count but lead to different destinations. Summing enclosed
pixels instead of measuring the largest region is a meaningful counterfactual.

## Teaching and sampling

The first demonstration contains four bodies with equal bbox and foreground
area: one three-cell hole, separate holes of areas two and one, three isolated
one-cell holes, and a three-cell boundary-connected notch. A solid rectangle
teaches the solid exception. Their labels identify all three settings.

The second demonstration supplies a cavity diagonally adjacent to an exterior
gap, an L-shaped cavity, a vertical cavity, a solid object and an open object.
These reject eight-neighbor gap connectivity, requiring every gap to qualify,
and using cavity width or height instead of area. Solid and open shapes both
change starting halves between the first two demonstrations, exposing both
nearest-edge and always-switch-sides shortcuts. Row order, positions, palette,
body widths, cavity positions and reflections vary deterministically with seed.
The first two backgrounds differ, and the second demonstration uses multiple
foreground colors while retaining a color shared by both destination classes.

All input randomness is independent of the private threshold. Requests support
**2–6 demonstrations and 1–4 queries independently**, defaulting to **3 and 4**.
The first two demonstrations carry the teaching contract. Query profiles are
19×19, 23×27, 27×29 and 30×30. The larger profiles contain six/seven objects,
four bodies spanning 25–27 columns at 30×30, bent/vertical cavities and tightly
distributed row bands. They exercise substantial content, not just blank
padding. Backgrounds are uniquely modal and exclude output colors 2 and 3;
row bands keep docking destinations collision-free.

There is no new canonical size override. These size profiles belong to the
separate native candidate. The sampled input grammar deliberately excludes
overlapping row spans, mixed-color composite objects and interactions between
docked objects. It is a constructive motif family, not unrestricted polyomino
sampling. Finite-rival checks do not prove uniqueness against all possible rules
or establish a training improvement.

## Files and executable checks

- `adapter.py` loads the adjacent prototype by exact path.
- `prototype.py` supplies the deterministic sampler, Python label claims,
  executable Racket settings, and named alternative programs.
- `canonical.rkt` preserves the selected reference bytes.
- `promotion.json` declares settings, independent count bounds and resources.
- `self_review.py` replays labels and finite rivals through protected Racket,
  checks paired inputs and query-prefix consistency, and emits safe first-turn
  previews plus private controller-side evidence. Reuse it after future edits.
- `evidence/manifest.json` is the native source/evidence inventory. Native
  qualification and the causal witness are retained in the packet's `checks/`.

Run these from the outer packet folder with its ready Python interpreter:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/7c7f1f574a18/tests/test_parametric.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/7c7f1f574a18/workspace/parametric/self_review.py \
  --demos 2 --queries 4 --out ../checks/7c7f1f574a18/new-self-review

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  7c7f1f574a18 --demos 3 --queries 4 \
  --out ../checks/7c7f1f574a18/new-qualification --summary
```

After source changes, refresh the inventory with the native `parametric manifest`
command and its exact-hash replacement guard before qualifying. Existing output
directories are refused; retain prior failures and choose a new destination.

## Visibility and handoff

The controller stores all four query/answer pairs privately. A public first turn
contains demonstrations and **only the first query input**; it has no setting,
seed, program, answer, total-count hint or future input. Its name hashes the exact
visible bytes. Generating one query versus four leaves that first turn identical.
Later query inputs belong in subsequent turns after the preceding answer. This
prototype supplies evidence/projection, not a training loop or turn controller.

Passing native qualification makes this candidate ready for owner intake.
The owner must qualify and accept the exact integrated bytes before using native
accepted-family export. The reviewer does not refresh approval hashes or claim
acceptance. Once accepted, a four-query production command is:

```bash
arcpuzzles parametric export 7c7f1f574a18 --count 3 --seed 41 \
  --demos 3 --queries 4 --out var/datasets/hole-area-s41
arcpuzzles parametric verify-export var/datasets/hole-area-s41
```

The native export is a controller dataset containing all query inputs; consumers
must apply sequential reveal. Acceptance and export do not activate training.
