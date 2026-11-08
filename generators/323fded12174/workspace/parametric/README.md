# Row ranking with an anchor-color dependency

This is a separate two-setting prototype for `323fded12174`. It keeps the
selected production generator, its approval, and its canonical data unchanged.
The default program is the exact Catalog source in `canonical.rkt`.

## Meaning of the parameter

| `rank_by` | Operation |
| --- | --- |
| `occupancy` (default) | Stable-sort complete input rows by descending number of nonzero cells. |
| `anchor_color` | Select the unique row with greatest nonzero occupancy. Find that row's unique most frequent **nonzero** color. Stable-sort the original complete rows by descending count of that selected color. |

Every output row preserves every cell, zero, gap, and original column position.
Equal scores keep input order. The anchor is selected before sorting and is
included in the final sort like every other row. It need not finish first:
each core demonstration has another row containing more of the selected color.
This makes the anchor/color selection determine the downstream ranking.

For example, if row occupancies in source order are `[3,4,7,3,5,2]` and the
anchor's selected-color counts are `[0,4,3,2,2,0]`, occupancy orders the rows
`[2,4,1,0,3,5]`, whereas anchor-color ranking orders them `[1,2,3,4,0,5]`.
The equal-2 rows and equal-0 rows retain source order in the second output.

## Separate grammar extension

The existing production generator keeps its five canonical dimension/palette
profiles and distinct occupancies. This prototype explicitly extends that
support. Its validator requires:

- Height **3..30**, width **5..30**, rectangular exact integer colors **0..9**.
- At least three nonzero colors overall.
- At least one foreground cell and one zero in every row.
- A unique row of maximum nonzero occupancy.
- At least two nonzero colors in that anchor, with a unique nonzero modal color.

Lower rows may tie in occupancy. Selected-color counts may tie, including at
zero; these ties are deliberately taught. Zero may be the most common value
in the anchor but cannot be selected as the target color. An input already
ordered under a setting is lawful, so some small query outputs are identities.
Both programs are total on this admitted grammar. The generator samples a
constructive subset; it does not claim to enumerate every lawful grid.

## API and count contract

```python
program({'rank_by': 'occupancy'})
program({'rank_by': 'anchor_color'})
episode = generate(17, {'rank_by': 'anchor_color'}, demos=3, queries=4)
```

`generate(seed, settings, demos=3, queries=4)` supports **3..6 demonstrations**
and **1..4 queries**, independently. Seeds are literal integers in
`0..2**63-1`; booleans, floats, unknown settings and unsupported counts raise
`ValueError`. Settings contain exactly `rank_by`.

Each call constructs the full six-demo/four-query input bank before slicing.
The seed's input bank is independent of the setting and requested counts.
Changing either count preserves the prefix of the same split, and the two
settings have identical inputs. Every complete bank contains ten distinct
inputs. Native qualification can therefore compare meanings without an
input-distribution cue. The adapter loads the adjacent prototype by exact path
and content-bound module name, avoiding cached modules from other families.

Outputs returned by `generate` are deterministic Python **claims**. Generation
does not start a Racket subprocess. The protected worker, focused checks and
independent audit execute the emitted Racket programs separately.

Other useful APIs are `reference(grid, settings)`, `occupancy_reference(grid)`,
`anchor_color_reference(grid)`, `row_facts(grid)` and `self_check(grid)`.
`row_facts` reports occupancies, anchor index/color, its nonzero color counts,
and every row's selected-color count. `teaching_survivors` is the prototype's
bounded finite-rival guard, not a proof over all possible interpretations.

## Three core demonstrations

The minimum lesson uses three constructed scenes with 7..9 rows each. Their
count scale, width, nonzero palette, anchor position, row order, and occupied
cell layout vary with the seed. Layouts include contiguous runs, scattered
cells, and separated boundary cells; output columns remain intact.

Each scene contains a mixed anchor, a lower-occupancy row that outranks it in
selected-color count, a concentrated distractor of another color, equal
selected-color scores with unequal occupancies, and equal-occupancy rows with
different contents. The lower-occupancy member of a selected-color tie occurs
first, exposing an incorrect occupancy secondary key. Extra rows use additional
colors. Anchor-color numeric ranks differ across the three roles, and its first
nonzero pixel deliberately has a different color from its mode.

The third scene has enough zero cells in the anchor to make the overall modal
value zero. The correct cue still comes from the nonzero colors. Random row
orders and a bounded screen reject fixed-position cues and lexicographic ties.

The prototype independently screens the three demonstrations under both
settings against 20 predeclared candidates: dominant frequency, mixed-row
priority, color-diversity priority, ascending score, first-row cue, last-row
cue, most-color-concentrated-row cue, second-highest-occupancy cue, global mode,
anchor's first/minimum/maximum color, anchor mode including zero, presence,
score fraction, reversed ties, lexicographic ties, occupancy secondary ties,
left justification, and within-row color sorting. Cue candidates are equivalent
to the default setting by definition; normalized occupancy and its occupancy
secondary key are also equivalent there. Equivalent candidates are exempt from
refutation, and the audit reports that distinction.

The finite screen uses at most 128 three-scene attempts. Additional bank inputs
use at most 32 attempts each for grammar and novelty. Exhaustion raises visibly;
there is no silent count reduction or setting-dependent retry stream. The
returned `sampling` field records actual teaching and novelty attempt counts.

## Queries and scale

Query 0 is literal **3×5** for seed 0. Other seeds use varying small 3..6 by
5..9 grids. Query 1 varies medium dimensions, query 2 is a large rectangle,
and query 3 is **30×30**. The maximum query has thirty distinct, foreground-bearing
rows with varied occupancies and color counts. Its large size is part of the
row-ranking problem rather than inert padding.

The other three demonstrations vary small, medium, and larger dimensions.
Random scene construction changes row occupancy/count profiles and pixel
arrangements as well as palette labels.

## Executed focused evidence

From the outer packet root:

```sh
WORK/.venv/bin/python review.py run --receipt checks/323fded12174/family-first-command.json python3 -m pytest -q generators/323fded12174/tests/test_parametric_323fded12174.py
WORK/.venv/bin/python review.py run --receipt checks/323fded12174/family-sampler-final-command.json python3 ../checks/323fded12174/family_sampler_probe.py
```

The focused suite passed **31 tests**. Its protected Racket check evaluated
**12 labels**: a literal stable-tie fixture, three core demonstrations, the
minimum query and the dense maximum query under both settings. Other focused
checks cover exact default bytes, request rejection, deterministic shared
banks/prefixes, lawful grammar and substantive maximum size. The initial missing
implementation result is retained as `family-red-command.json` / `family-red.log`.

The independent Python-only sampler checked seeds **0..23**, both settings,
and requests **(6,4), (3,1), (3,4)**: **144/144 passed**, with 240 unique inputs,
480 unique claim-labeled pairs, and 96 unique query inputs. First queries had
24 distinct inputs over 11 shapes. Core scenes covered all nine possible
nonzero target colors, all positions of their 7..9-row anchors, and 41 distinct
occupancy/target-count profiles. The dense queries contained **517..624 nonzero
cells**. Maximum observed attempts were **2/128** for teaching and **2/32** for
novelty. Identity first-query counts were 5/24 for occupancy and 3/24 for
anchor-color ranking; the minimum demonstrations still distinguish the settings.

`WORK/checks/323fded12174/family-sampler-final.json` binds the exact implementation
and test hashes and records every request and attempt count. This sampler is
Python-only; it does not add protected execution evidence. Independent rival
audit, native qualification, export and causal replay have their own source-bound
receipts. This README does not turn prototype evidence into acceptance or
training admission and makes no global identifiability or measured-learning
claim.
