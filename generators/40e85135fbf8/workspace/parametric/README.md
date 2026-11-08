# Header equality and largest connected blocks

This is a separate native proposal beside the selected version 4.0.0 production
generator. Its default preserves the canonical Racket source byte for byte.
The new episode parameter is `selection_mode`, fixed across all demonstrations
and queries: `all_matches` or `largest_blocks`.

## Executed rules and sequential dependence

`all_matches` drops the first row and first column. Each remaining position takes
its row-header color when that color equals its column-header color; otherwise
it is zero. Header equality, output dimensions and original color identity remain
the central reasoning in both settings.

`largest_blocks` first constructs that same equality matrix. It then discovers
four-connected monochromatic nonzero components, measures their cell areas,
and retains every component tied for the largest area anywhere in the matrix.
Retained cells keep their color and location; all other cells become zero.
If no headers match, the output is blank with the full cropped dimensions.

The computed equality matrix is the intermediate consumed by component selection.
Reading the original blank interior instead removes all candidate components and
changes a nonblank qualified answer. The native witness retains the input,
intermediate, actual output and protected-Racket counterfactual.

For this grammar, each component is a Cartesian product of maximal same-color
header runs. Its bounding-box area equals its cell count; monochromatic four-
and eight-neighbor components also coincide. Those equivalent algorithms are
excluded from the wrong-rule bank. Combining differently colored diagonal blocks
under binary eight-neighbor connectivity can change the answer and is tested.

## API and semantic domain

`program(settings)` returns complete `(rule! ...)` source. `generate(seed,
settings, demos=3, queries=4)` returns private `train`, `test` and
`program_solution`. `mirror` is the Python claim implementation; `analyze`
exposes row and column headers, the equality matrix, component cells and areas,
the maximum area, retained component indices and the final output.
Native qualification independently executes every retained label through Racket.

Inputs are rectangular Python lists, 2..30 cells on each axis, with exact integer
colors 0..9. The corner is zero; every other cell in the first row and first
column is nonzero; the remaining interior is entirely zero. Arbitrary palettes,
repetitions, separated runs, private header colors, single-color headers and
disjoint header sets are lawful. The output is 1..29 on each axis. A 30×30 input
has 58 nonzero header cells by construction; size stress concerns the header
runs, constructed matrix and component competition, rather than input fill.

Settings contain exactly `selection_mode`. Seeds are exact integers in
`0..2**63-1`. The contract supports **3–6 demonstrations**, default three, and
independently **1–4 queries**. Booleans used as numbers, malformed grids, unknown
settings and unsupported counts are rejected. Every returned grid is fresh.

## Constructive teaching and query coverage

Three demonstrations combine complementary distinctions:

1. A unique area-14 block of size 2×7 beats an area-12 block of size 3×4.
   The losing color has greater total area across separated components, while
   smaller pieces of the winning color must still disappear. Both axes have
   private header colors whose false ordinal-rank match would create an even
   larger block. This distinguishes area from short-side length, per-color
   aggregation, whole-color retention and independent color-rank matching.
2. Four blocks of one color and a block of another color tie at area six,
   using 2×3 and 3×2 aspect ratios. A 5×1 component loses. This teaches global
   ties across colors and rejects height, width, perimeter and first-winner rules.
3. All genuine components have unit area. Private headers create an all-zero
   output border on each axis, teaching full output extent and unit components.

Core grids use independent color-role choices, row/column header reversals and
transposition. The first two can reach 24 cells on one axis: that is the teaching
cost of combining several distinctions within three examples. Up to 64 candidate
triples are checked against the finite independently authored rival bank using
demonstrations alone. Exhaustion raises an explicit error; query answers never
participate in choosing the teaching triple.

The first proposed core was refused by this check because foreground cropping
and shorter-side ranking survived. The before snapshot and Python diagnostic
are retained under `checks/40e85135fbf8/cover-before/`; they are not represented
as successfully emitted or Racket-qualified episodes. A failing geometry
regression and its repaired passing run record the change.

Additional demonstrations use 7×9, 11×15 and 17×23 inputs. Four queries use 5×7,
13×17, 23×27 and 30×30 inputs, shuffled by an independent seed stream. Small
queries include one-color and empty-match cases. Large queries place shared
header runs at both ends of both axes, creating substantive matching content in
all four quadrants with competing components and private-color distractors.
Counts select stable prefixes, settings share identical inputs, and bounded
duplicate checks keep every requested input distinct.

Transpose, reversing one header axis and nonzero color permutations are lawful
semantic transformations and have independent checks. Rotating the raw framed
input generally moves headers out of their declared positions.

## Reusable checks and replay

`rivals.py` contains an independent flood-fill oracle, hand-built fixtures,
26 canonical-setting rivals and 48 largest-block rivals, with executable Racket
versions. `audit.py` checks the supported count cross-product at eight seeds,
demonstration-only identification, independent labels, stable input prefixes,
source bindings, observed palette/rank coverage and meaningful maximum-size
content. Protected execution covers canonical pairs, fixtures, distinguishing
rival cases, legal transformations and representative generated episodes.

A separate frozen 30-hypothesis review lives under
`checks/40e85135fbf8/final-review/`. It was authored before reading the prototype
or the teaching bank. The packet-local `checks/projection_edges.py` exercises the
saved one-query public views and export/verifier mutation boundaries.

From the outer packet folder, choose fresh output paths:

```sh
WORK/.venv/bin/python review.py task-tests 40e85135fbf8 --phase after --out ../checks/40e85135fbf8/task-tests-replay
WORK/.venv/bin/python review.py run python3 generators/40e85135fbf8/workspace/parametric/audit.py --out ../checks/40e85135fbf8/audit-replay.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 40e85135fbf8 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/40e85135fbf8/qualification-replay --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/40e85135fbf8/qualification-replay/qualification.json --out ../checks/40e85135fbf8/preview-replay
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/40e85135fbf8/preview-replay
```

Use the native manifest helper after source edits, before qualification. Deliver
only the selected `preview/public/<hash>.json` on each query turn. Settings,
seeds, programs, answers and other query inputs remain controller-private; the
first view matches single-query use exactly.

The recorded seed/rival checks are finite evidence. They do not establish
universal identification, all-seed success or measured learning gains. Owner
exact-source acceptance and training admission remain separate steps.
