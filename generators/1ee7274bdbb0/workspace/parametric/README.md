# Native marked-tile turns and settling — 1ee7274bdbb0

The episode fixes two parameters:

| Parameter | Values | Canonical default |
|---|---|---|
| `turn` | `cw`, `ccw` | `cw` |
| `post` | `none`, `settle_down` | `none` |

Full color-9 rows and columns delimit uniform square tiles. In each tile,
color 2 is the complete motif and color 3 is a control marker. Recolor motifs
to 8 and remove markers. A tile containing any marker turns its motif one
quarter-turn about the **whole tile** in the chosen direction; an unmarked tile
does not turn. `settle_down` then translates the entire resulting motif down by
`tile_size - 1 - maximum_occupied_row`. All disconnected parts move together;
holes and relative offsets remain. Empty motifs remain empty. Preserve the
divider lattice. `cw/none` returns the exact selected canonical program text.

## Dependency and order

**A** identifies marker presence and produces the selected, rotated-or-unrotated
motif. The **intermediate** is that transformed occupied-cell set. **B** computes
its lowest occupied row and applies the resulting common downward displacement.
The displacement depends on A's geometry. Settling the raw motif before turning
can give a different displacement and final location. The protected causal
witness swaps exactly those two operations with the same marker predicate,
quarter-turn and settling function. This is a geometric state dependency, not
iterative simulation or a claim about training gains.

## Native grammar and size limits

Input axes are 3–30; tiles are uniform squares of size 3–30. Colors are exact
integers in `{0,2,3,9}`. Dividers are single full lines, with no outer frame,
adjacent dividers or stray 9s inside tiles. A single tile without dividers is
allowed as an explicit extension. Inputs may contain heterogeneous marker
counts, empty motifs and arbitrary motif topology; all settings remain total.
The unchanged production 5.0.0 grammar, controls and six-demo schedule remain
separate, including its existing call-validation audit disposition.

A multi-tile axis has length `n * (s + 1) - 1`. Exact length 30 would require
`n * (s + 1) = 31`, so a regular square-tile 30×30 scene must be a **single
30×30 tile**. The bank therefore also includes 29×29 with nine 9×9 tiles for
large multi-tile branch decisions. Each 30×30 input has over 300 motif cells
spread across all quadrants. Its motif leaves positive settling distance in
both turn directions; boundary marker cells touch the outer canvas edges.
These cases execute substantial geometry, rather than padding a small tile.

## Constructive teaching bank

`generate(seed, settings=None, demos=3, queries=4)` accepts exact integer seeds
0 through 2**63−1, independently 2–6 demonstrations and 1–4 queries. Settings,
input construction and query order use separate deterministic random streams.
The full bank is constructed before slicing, with matched inputs across all
four settings. There is no rejection loop or silently shortened episode.

The first core is an 11×17 lattice of six 5×5 tiles; the second is a 7×11
lattice of six 3×3 tiles. Each includes marker counts 0/1/2/3 and four marked
tiles out of six, with connected/disconnected, symmetric/asymmetric and
different-sized motifs. Centered and off-diagonal markers, marker/output
overlap, markers outside the output, uncovered output, holes, and disconnected
relative offsets are all taught. One symmetric tile may be locally ambiguous;
the complete two-demo output vectors distinguish every setting. Witnesses are
checked after the chosen post-operation, since settling can erase a raw turn
distinction. Independent row/column permutations preserve each intact role.

Additional demos are 3×3, 19×19, 29×29 and 30×30. The four queries are 3×11,
17×11, 27×27 and 30×30 in a separate seeded order. Later multi-tile profiles
construct connected growth, sampled subsets, rings and staircases with varied
marker locations/counts. Growth adds one available frontier cell per step and
has a finite cell-count bound. The two 30×30 roles have different marker counts.
Every query is distinct from all demos and other queries.

The fixed core templates have a bounded placement bank; larger profiles vary
their masks and markers constructively. This does not claim uniform sampling
of all legal masks, every legal dimension or universal rule uniqueness.

## Verification and use

Use the two explicit native test files, `tests/test_native_family.py` and
`tests/test_native_audit.py`. The task-local audit has an independent oracle and
exact executable rivals for marker branches, transforms, pivot/bounding-box
shortcuts, ordering and non-rigid gravity. It uses only the first two demos for
teaching decisions and executes the complete six-demo/four-query bank for labels.
Evidence is under `checks/1ee7274bdbb0/`; source inventory is
`evidence/manifest.json`. Python output claims are independently replayed by
native Racket qualification.

From the outer packet folder, with its selected Python environment:

```bash
python3 review.py run python3 -m pytest generators/1ee7274bdbb0/tests/test_native_family.py generators/1ee7274bdbb0/tests/test_native_audit.py
python3 review.py run python3 -m arcpuzzles parametric qualify 1ee7274bdbb0 --demos 6 --queries 4 --out ../checks/1ee7274bdbb0/qualification-new --summary
python3 review.py preview-public export --qualification ../checks/1ee7274bdbb0/qualification-new/qualification.json --out ../checks/1ee7274bdbb0/preview-new
python3 review.py preview-public verify --bundle ../checks/1ee7274bdbb0/preview-new
```

Choose fresh output paths. Reveal one selected `public/<sha256>.json` file at a
time; keep answers, settings, reference programs, future queries and directory
listings with the controller. The existing native exporter adds no new turn
controller. Owner qualification and fresh acceptance of both exact integrated
sources remain separate. No training admission or activation follows.
