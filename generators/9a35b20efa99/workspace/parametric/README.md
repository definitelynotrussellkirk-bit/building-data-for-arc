# Orbit stamping in a fixed or source-derived frame

This is a separate native prototype for `9a35b20efa99`. It preserves the exact
selected canonical program in `canonical.rkt` and the production generator's
version `2.0.0` authority. Owner qualification and fresh acceptance remain
required after integration; reviewer qualification does not admit training data.

## Rule and input-dependent intermediate

Locate the unique color-9 anchor and the monochrome source template. Remove the
anchor before cropping the template, preserving zeros and holes within its bbox.
The private episode setting determines the frame:

| `orientation_frame` | Crop consumed by stamping |
|---|---|
| `fixed` | The input crop, unchanged; exact canonical default |
| `source_side` | Rotate the crop clockwise by above=0, right=1, below=2, left=3 quarter-turns, according to its position relative to the anchor |

Stamp the resulting crop's 0/90/180/270-degree rotations in upper-left,
upper-right, lower-left and lower-right order. All offsets use the dimensions
`ch,cw` of that one resulting crop:
`(-ch-1,-cw-1)`, `(-ch-1,1)`, `(1,-cw-1)`, `(1,1)`.
The dimensions are not recomputed separately for each output stamp. Preserve the
anchor and clear the original source. Only nonzero crop cells are pasted.

For the alternative, step A derives the source side, constructs the oriented
mask and computes its dimensions. Step B consumes that mask and those dimensions
to place all four copies. Skipping orientation on a rectangular left/right source
changes the final geometry. The fixed setting also consumes the actual cropped
mask: substituting its filled bbox changes the stamped shapes. These are bounded
executed causal counterfactuals, with the interpretation retained as authored
metadata. The alternative is contextual orientation, not iterative simulation.

The assigned public-evaluation focus is `142ca369`. Its supplied examples suggest
direction derived from visible object/context relationships; that principle
motivates the source-side frame. This is an interpretation used for inspiration,
not verified ancestry or equivalence to that task's rule.

## Supported domain and teaching cost

Inputs are exact-integer ARC grids with axes 6..30, background zero, exactly one
color-9 anchor, and one four-connected monochrome template colored 1..8. The
template has at least three cells and bbox axes 2..14. It is separated by at least
one blank row or column on a unique cardinal side, aligned with the anchor on
the other axis. If `m` is its larger bbox axis, the anchor has conservative margins
`m+1 <= row <= height-m-1` and the analogous column bounds. Both settings then
fit without clipping. Wide crops may produce overlapping same-color stamps;
the rule retains nonzero-paste union behavior.

`adapter.generate(seed, settings=None, demos=4, queries=4)` accepts exact integer
seeds in `0..2**63-1`, demos `4..6`, and queries `1..4`. An omitted setting uses
seed parity once per episode. Settings share identical input banks. Six demos
and four queries are constructed with independent local random streams before
slicing; outputs are fresh and global RNG state is preserved.

Four demonstrations are deliberate: each source has only one side, so this
prefix explicitly teaches all four side branches. Above/right share one
asymmetric rectangular crop, canvas, off-center anchor and color; below/left
share a different crop with an enclosed hole and a different color. Optional
demos add a narrow branch and scaled stairs. Query roles use 6x6, 18x20, 25x27
and 30x30 canvases, with template areas 3, 37, 66 and 140. The largest template
is 14x14; its executed output has 561 occupied cells and spans the whole 30x30
canvas. The input itself has 141 occupied cells, not canvas-wide coverage.

At the minimum and maximum, separation/margin geometry allows only above/left
source placements. These queries use opposite sides; the middle two supply
right/below. Every complete query bank therefore covers all four sides. The
complete bank is independently shuffled before prefix selection. This is a
structured constructive family with varying orientations, palettes, placement,
geometry and topology, not an exhaustive connected-polyomino sampler.

## Run, review and project public turns

From the extracted packet's outer directory, payloads run in `WORK/repo`.
Choose fresh evidence destinations for every run:

```sh
WORK/.venv/bin/python review.py run --receipt checks/9a35b20efa99/recheck.json \
  python3 -m pytest generators/9a35b20efa99/tests/test_native_family.py \
  generators/9a35b20efa99/tests/test_native_sampler.py \
  generators/9a35b20efa99/tests/test_native_adapter.py -q

WORK/.venv/bin/python review.py run --receipt checks/9a35b20efa99/rival-recheck.json \
  python3 generators/9a35b20efa99/workspace/parametric/audit.py \
  --seed 0 --seed 17 --out ../checks/9a35b20efa99/rival-recheck

WORK/.venv/bin/python review.py run --receipt checks/9a35b20efa99/requalify.json \
  python3 -m arcpuzzles parametric qualify 9a35b20efa99 --seed 0 --seed 17 \
  --demos 4 --queries 4 --out ../checks/9a35b20efa99/requalification --summary
```

The generic auditor reads the contract's qualification demo count when omitted,
executes labels and rivals through protected Racket, caches program/input pairs,
and records source hashes. It separates demo refutations, query conflicts,
finite consistency and execution errors. Its programs and labels are private.
The maximum-count boundary probe measures actual occupancy/span/contact against
the declared background and handles empty outputs; `--out` must be fresh.

Use the packet's current `preview-public export` with the four-query qualification.
Its private manifest permutes paired query inputs/answers, and each public file
contains demonstrations plus one current query input. Presentation seed, order,
future queries, settings, programs and answers remain controller-only. To stop
after one query, select the first turn from that same complete-bank presentation.
The public probe checks paired ordering, equal first-turn bytes for one-query
versus full presentation, hidden/future-field invariance, presentation-seed
independence of public IDs, and temporary corruption rejection. Serialized
verification does not claim another Racket replay.

Current source/evidence is inventoried by the native manifest. Frozen baseline
sources and independent shortcut probes remain under `checks/9a35b20efa99/`.
Finite audits and qualification do not prove all-seed success, unique induction
over all programs, or measured learning improvement. Production batteries are
outside this prototype-only change.
