# Enclosed-region selection

This opt-in native family extends the selected enclosed-background task with
one private, episode-fixed parameter:

| `selection` | Transformation |
|---|---|
| `all_enclosed` | Exact canonical Racket program: recolor each qualifying color-1 object to 8. |
| `largest_enclosed_region` | Score each object by its largest individual qualifying background region; recolor every object tied for the largest positive score. |

A qualifying region is an entire **four-connected color-9 component** lying
strictly inside an object's bounding box. The program preserves the background,
unselected objects and input dimensions. It recolors whole objects, including
their connected branches, rather than filling their holes.

The default program is copied byte-for-byte from the selected canonical
authority. The reviewed production generator and its control API are separate
from this adapter.

## Meaningful dependency

First discover the complete background components and measure the enclosed
regions associated with each object. Their largest individual areas form an
input-dependent score vector. Global comparison of those scores then selects
the objects to recolor, including all positive ties.

The two mandatory teaching scenes separate this rule from plausible shortcuts:

1. One irregular object has a hole of area 4; a larger object has two holes of
   area 3 each; a large open-U object has no enclosed region. The largest-region
   rule selects the first object, even though the second has greater total hole
   area and the open object has background pixels inside its bbox.
2. A missing-corner ring has a unit hole under four-connectivity; another object
   has two unit holes. Both have maximum individual area 1 and must be selected.
   This teaches all ties, unit holes, four-neighbor topology, and the difference
   between maximum area and summed area.

`largest_total.rkt` is a private counterfactual used only for causal verification.
It replaces each object's maximum individual region area with the sum of its
enclosed-region areas, leaving global winner selection unchanged. Executing
both programs on the same scenes shows the effect of the wrong intermediate.
It is not an additional accepted or exported parameter setting.

## Sampling and public projection

The shared prototype domain uses color 9 as background and color 1 as foreground,
on 9–30 by 11–30 canvases. It contains 2–3 hole-bearing objects and 1–4 negative
objects, with disjoint object bounding boxes, an irregular positive and an
open-bbox negative. These explicit invariants supplement the base validator.

`generate(seed, settings, demos=3, queries=4)` exposes independent **2–6 demo**
and **1–4 query** counts. Seeds are exact integers in `0..2**63-1`; booleans,
floating-point counts and undeclared settings are rejected. Input RNG streams
are independent of settings and requested query count. Query profiles include
9×11, 12×16, 22×26 and 30×30; the largest profile contains substantial large
cavities and distributed objects across the canvas.

`public_view(episode, query_index=0)` emits only demonstrations and the current
query input. It omits hidden settings, seeds, programs, query answers and future
queries. The first public view is identical for one-query and four-query calls.
The existing controller owns reveal timing; this adapter adds no turn controller.
Use `reviewer_support.public_challenge_bytes` for exact serialization and its
corresponding hash for public filenames. Complete four-query examples stay private.

Sampling uses a bounded constructive shape family, with translations and
reflections. The two mandatory demonstration geometries remain fixed up to
those transforms. Generated queries have untied largest-region winners; all-tie
behavior is exercised by the mandatory tie demonstration, literal geometry tests
and causal witness. This prototype does not claim broad shape diversity,
universal identifiability or measured learning benefit.

## Reproduce and qualify

From the outer packet directory, using its verified Python interpreter:

```bash
python3 review.py run python3 -m pytest \
  generators/9af68e46cf69/tests/test_parametric.py -q
python3 review.py run python3 \
  generators/9af68e46cf69/workspace/parametric/verify.py check \
  --out ../checks/9af68e46cf69/focused-new
```

The reusable verifier executes both settings through protected Racket, checks
canonical examples and private labels, fits finite competitors on demonstrations
only, checks both rules on the input union, verifies public/private invariance,
and saves private examples and hash-named one-query public files.

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 9af68e46cf69 \
  --evidence generators/9af68e46cf69/workspace/parametric/evidence/current \
  --include generators/9af68e46cf69/tests/test_parametric.py \
  --reported-checks 'Use the exact focused checks actually executed'
python3 review.py run python3 -m arcpuzzles parametric qualify 9af68e46cf69 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/9af68e46cf69/qualification-new --summary
python3 review.py run python3 \
  generators/9af68e46cf69/workspace/parametric/verify.py witness \
  --qualification ../checks/9af68e46cf69/qualification-new/qualification.json \
  --out ../checks/9af68e46cf69/sequential-witness-new.json
```

Use new output directories. Replacing an existing inventory requires its exact
current SHA-256 with `--replace`. The native qualification and its sibling
execution receipt, current inventory and causal witness accompany the reviewer
return. After integration, the owner must freshly qualify and accept the exact
live source. Finite teaching checks establish neither universal uniqueness nor
measured learning benefit, and no training admission is claimed.
