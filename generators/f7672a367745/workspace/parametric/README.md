# Rectangle reconstruction and area-selected fills

This native family preserves the exact canonical rectangle-outline program and
adds one episode-fixed rule parameter:

| `fill_policy` | Output |
|---|---|
| `outline` | Draw every eligible rectangle border in its marker color. This is the byte-exact canonical default. |
| `largest` | Fill every rectangle tied for greatest inclusive area; outline all others. |
| `smallest` | Fill every rectangle tied for least inclusive area; outline all others. |

## Semantics and dependency

For each nonzero color occurring exactly twice, reconstruct its inclusive
bounding box from those two cells. Its height and width include both endpoints;
its area is `height * width`. The alternative policies compare these areas
across all eligible colors. All tied extremes are selected. A single eligible
rectangle is both the largest and the smallest, so either alternative fills it.

The sequential dependency is **same-color marker pairing → reconstructed boxes
and their areas → global extreme selection → filled or outlined construction**.
Selection cannot be determined from the two marker counts, which are identical
for every eligible color. Perimeter, width, height, corner-span product and
interior area can give different rankings. The first demonstration deliberately
reverses the area and perimeter rankings. Its wrong-intermediate causal replay
substitutes perimeter scores while holding the input, pairing and painting code
fixed.

All boxes and scores are computed from the original input before painting.
Colors paint in ascending numeric order, matching the canonical `grid-colors`
primitive. A later color overwrites only cells it paints; an unfilled interior
does not erase earlier paint. This also defines overlapping-box behavior.

## API domain and generated grammar

`apply_claim` accepts rectangular Python lists of lists with side lengths 1–30
and literal integer cells 0–9. Booleans, floats, tuples and ragged grids are
rejected. All-zero inputs return all zero. Colors occurring once or more than
twice are ignored, exactly as in the canonical executable. Two cells in one
row or column produce a line. These wider API cases are covered by literal
protected-Racket regressions.

Generated lessons use the narrower, source-aligned grammar: disjoint rectangles
with interiors, each identified by two diagonally opposite markers of a unique
color. This avoids introducing an untaught overlap-priority rule into the
demonstration distribution. With nine nonzero ARC colors, such an input has at
most 18 occupied cells. The 30×30 stress case uses all nine colors with rectangle
geometry spread across the grid and contacts at all boundaries; its expanded
output measures substantive coverage rather than padded dimensions.

The three required demonstration roles are:

1. Two rectangles of dimensions 4×10 and 6×7. Their areas are 40/42, while their
   perimeters are 28/26, reversing the ranking.
2. One interior-bearing rectangle, teaching the single-object case.
3. Six rectangles, including ties at both extremes: 3×8 and 4×6 have area 24;
   6×6 and 4×9 have area 36. Two middle rectangles have areas 28 and 32.
   Different aspect ratios distinguish competing metrics, and the extreme
   groups occupy opposite diagonal quadrants.

The selected and unselected area ranges overlap across demonstrations, ruling
out a fixed monotone area threshold. The middle areas distinguish true extrema
from filling everything except the opposite extreme, and from mean or median
splits. Geometry-preserving transforms, palettes, and marker diagonals vary
without changing the lesson roles. Additional demos and four novel queries
supply count, geometry and boundary variation.

The earlier four-box D2 had only two distinct area levels. Protected execution
demonstrated that a non-opposite-extreme rival then fitted all three demos and
changed 38 cells on query 2 under each alternative policy. That original lesson,
both executable programs and their outputs remain in `checks/f7672a367745/middle-gap.json` for alternative-answer reuse. The six-box repair changes D2
without increasing the three-demo requirement; other bank inputs are preserved.

## Deterministic native interface

`adapter.py` loads its exact adjacent `native_family.py`; that module loads its
exact adjacent sampler. There are no imports from previous checkouts.

- `program(settings)` returns the complete selected Racket rule.
- `generate(seed, settings, demos, queries)` returns private input/output pairs
  and the exact program. Python outputs are claims until protected execution
  verifies them.
- `apply_claim`, `describe`, `public_turn` and `rivals` support focused checks
  and the retained audit.
- Settings contain exactly `fill_policy`. Seeds are literal integers in
  `0..2**63-1`; demo counts are 3–6 and query counts independently 1–4.
- The sampler builds the complete six-demo/four-query bank before slicing.
  Inputs match across policies and count requests, and all ten bank inputs are
  distinct. Randomness is local and duplicate retries are bounded.

## Public projection and reusable audit

The public challenge contains only visible demonstration input/output pairs and
one query input. Settings, programs, query answers, future queries, total counts
and diagnostic metadata remain private. Public IDs depend only on canonical
public JSON bytes. The first public turn is identical for one-query and
four-query generation with otherwise matching arguments.

`audit.py` labels examples through the protected Racket runtime, checks Python
claims and all five saved canonical pairs, evaluates finite executable rivals
against demonstrations only, and exports strict one-query public records with
their private associations. Errors are failures, never refutations. Its verifier
rejects altered labels, private-field leaks, forged identifiers, duplicate
inputs, incorrect associations and orphan files. Literal overlap behavior is
tested separately; overlap-order rivals would be equivalent on the disjoint
generated grammar and are not presented as refuted teaching alternatives.

## Replay from the outer packet directory

```sh
WORK/.venv/bin/python review.py run python3 -B -m pytest -q \
  generators/f7672a367745/tests/test_native_adapter.py \
  generators/f7672a367745/tests/test_native_audit.py

WORK/.venv/bin/python review.py run python3 -B \
  generators/f7672a367745/workspace/parametric/audit.py \
  --out ../checks/f7672a367745/audit-replay --seed 0 --seed 17

WORK/.venv/bin/python review.py run python3 -B -m arcpuzzles parametric \
  qualify f7672a367745 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/f7672a367745/qualification-replay --summary
```

Choose unused output directories. Current command receipts, executed results,
source inventory, qualification and causal replay are retained in the return.
These are finite checks, not a universal learnability claim. The existing
historical `needs_evidence` disposition remains unchanged. Reviewer-ready
evidence requires owner qualification and acceptance of the exact integrated
source; this artifact does not activate training.

## Verified return status

Final-r3 passed **62 focused tests**. The protected audit verified **5 canonical
and 42 generated labels**, refuted **166/166 finite candidate comparisons** on
three demonstrations, and verified **24 public files**. All 12 repaired-selector
comparisons are refuted by D2. Native qualification passed six jobs with 78
protected evaluations. Wrong-perimeter causal cases change **36 cells each**
for largest and smallest policies, and native witness replay passed. Exact
integrated-source owner acceptance remains pending; training is not admitted.
