# Direct waves and corner relay

This is a separate native parametric adapter for `891a82451a8a`. The approved
canonical generator and selected reference are unchanged. `mode=direct` returns
the exact canonical Racket text, including its original whitespace.

## Rule and causal dependency

The cycle is `0, 5, 2, 8, 9, 6, 1, 3, 4`. Inputs have a uniform nonzero background
and one seed belonging to that cycle. The background differs from the seed.
The parametric grammar supports heights and widths from 5 through 30; the
unchanged canonical sampler retains its original 5 through 18 bounds.

| Episode-fixed mode | Transformation |
| --- | --- |
| `direct` (default) | Color every cell by seed phase plus Manhattan distance, modulo nine. |
| `corner_relay` | Compute the first wave, choose the corner with the lowest cycle phase, then emit a second Manhattan wave from that corner, starting with its first-wave color. |

Corner ties use row-major order: top-left, top-right, bottom-left, bottom-right.
Cycle phase means position in the cycle, **not** the numeric ARC color value.

The required dependency is **A: derive the four corner phases from the seed's
phase and location → intermediate: the ordered corner-phase vector and selected
corner → B: choose that corner as the second wave's origin and transfer its
phase**. Changing seed color alone can change the selected corner. Selecting a
corner before deriving these values, or ignoring seed phase, can change the
whole answer. The causal witness compares the actual alternate program with
the executable `ignore_seed_phase` counterfactual.

The implementation materializes the first wave. Only its four corner phases
are computationally necessary for selection; the complete intermediate grid
is not indispensable. The second wave is a diagonal stripe pattern because its
origin is a corner. This is a bounded compositional extension, not a claim of
iterative simulation or measured difficulty improvement.

## Lesson construction and the repaired teaching holes

`generate(seed, settings, demos=3, queries=4)` accepts 2–6 demonstrations and
1–8 queries independently. Use four queries for the requested training lessons.
Settings are fixed across the entire episode. Input sampling never reads the
selected setting: the same seed and counts give the same inputs in both modes.

Two constructively selected demonstrations refute 10 direct-mode and 19
relay-mode core rivals. These include wrong distance, phase, corner selection,
phase transfer, direction and several tie policies. Both core demonstrations
span a complete color-cycle transition, including wrap. A bounded search stops
with an explicit error after 384 candidate inputs; it never shortens a lesson.

The first implementation had two concrete learnability defects. A rule omitting
an unshown corner fit a two-demo lesson but failed its query. A different fixed
corner-priority order fit a three-demo lesson but disagreed on a tied query.
The original small lessons are retained privately in `evidence/current/` and
`audit.py` replays both interpretations through protected Racket.

The repaired policy adds a previously unshown winning corner in demonstrations
three and four. Four demonstrations therefore cover every corner. At two or
three demonstrations, queries use only corners selected by those demonstrations;
the family retains all four branches across episodes. This limits within-lesson
corner extrapolation in short lessons. Four-demo lessons permit all four winners.

In addition to the 29 core rivals, the sampler fits four fixed corner-omission
rules and all 23 alternative fixed corner-priority orders to demonstrations only.
It admits each query input only when the surviving rules agree with the intended
prediction. Query answers are never used to fit rivals. This also protects
against any globally fixed nonempty subset of corners: a surviving subset must
contain every demonstrated winner. It does not exhaust arbitrary input-dependent
pruning rules or all imaginable programs.

The first four query shapes are 5×5, 14×23, 23×18 and 30×30. They exercise corner,
edge and interior seeds; output colors cover the whole canvas, with repeated
cycle wraps and seed-to-corner propagation. Extra distractor seeds would violate
this family's grammar. The sparse input is inherent to the source task, not
padding added to satisfy a size test. All input grids in one episode are distinct.

## Run and verify

Run these commands from the outer packet directory, using its passing Python:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/891a82451a8a/tests/test_parametric.py

WORK/.venv/bin/python review.py run python3 \
  generators/891a82451a8a/workspace/parametric/audit.py \
  --out ../checks/891a82451a8a/new-audit

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  891a82451a8a --demos 3 --queries 4 \
  --out ../checks/891a82451a8a/new-qualification --summary
```

Choose new output paths for every execution. `audit.py` checks both settings,
seeds 0 and 17, demo-count endpoints 2 and 6, and four queries. It executes native
setting labels, core rival refutations, extra rival fits and both teaching-hole
repairs using the protected same-checkout Racket bridge. Its separate 12-seed
sampler probe is explicitly Python diagnostic evidence, not additional
Racket-verified training data. It also checks public projection, first-turn
equivalence, private-metadata independence and Boolean-cell rejection.

The adapter's in-process Python outputs are claims. Only protected qualification
or audit execution verifies them against Racket. Rebuild the native manifest
after changing any inventoried source or evidence, then qualify exact bytes.

## Public and private boundaries

`audit.py` writes opaque hash-named files under `public/` and `first_turn/`.
Names hash only canonical visible demonstration pairs and query inputs using
`reviewer_support`. Private settings, seeds, programs and answers never enter
those bytes or filenames. The corresponding map and execution evidence are
explicitly private.

The four-query public container is controller data. Give the model the matching
`first_turn/` challenge initially, then reveal only the next input after the
previous answer. Use the existing consumer; this adapter creates no training
loop or controller. There are no total-count or final-turn markers. For a fixed
seed, setting and demonstration count, the first-turn bytes are identical for
one-query and four-query generation. Changing the demonstration count may change
the query sampling constraints because it changes what has been taught.

## Acceptance boundary

Passing tests and native qualification are reviewer evidence. The owner must
integrate the exact source, retain canonical approval, rerun native qualification,
and perform fresh native acceptance. No local metadata or prototype inventory
substitutes for that step. This work neither admits training data nor changes a
training mixture. Finite rival coverage does not establish universal uniqueness.
