# Isolated islands, then enclosed-region area

This native adapter proposes two episode-fixed settings for `b28619e32f6f`:

| `island_policy` | Executed rule |
|---|---|
| `keep` (default) | The exact canonical Racket bytes: discover four-connected zero regions, leave exterior zero alone, color enclosed areas ≤8 cyan, ≤24 yellow, and larger areas green. |
| `absorb` | Remove original red cells having four orthogonal zero neighbors; recompute zero connectivity and areas on that intermediate grid, then apply the canonical classifier. |

The approved production generator and canonical authority are unchanged. The
adapter is a separate opt-in family. Its claimed Python labels are checked by
protected Racket; inventory, qualification, owner acceptance and training
admission remain distinct.

## Input grammar and teaching

Inputs use only 0 and 2, complete red rectangular boundaries, internal red
dividers/decoys and border-connected exterior zero. Both original and absorbed
grids pass the existing canonical validator in the bounded audit. There is no
palette reskin: red boundaries, zero background and the canonical output colors
retain their semantic roles.

The first two demonstrations construct complementary witnesses:

1. Areas 7, 8, 9, 23, 24 and 25, including stable wall-attached notches. These
   retain the exact thresholds after preprocessing under either setting.
2. Isolated islands at 8→9 and 24→25, a diagonal X that merges four pockets,
   a persistent domino, a persistent diagonal barrier separating two pockets,
   and one divided frame containing differently sized regions.

Rotations, reflections, placements, chamber order and incidental geometry vary
with the seed. Extra demonstrations use variable rectangular mosaics. Parameters
do not influence input RNGs. Supported counts are independently **2–6 demos** and
**1–4 queries**, normally **3+4**. Every input within an episode is distinct.
The two-demo minimum is a deliberate teaching budget; no long-demo tail is used.

Queries cover small transfer (minimum 4×4), varied mosaics, a fresh topology
scene, and substantive 30×30 stress with sixteen chambers across four divided
frames. The larger scenes occupy all four quadrants, include border contact,
vary shape/area/distractors, and typically transform hundreds of cells.
These are sampler profiles, not a claim to sample every lawful 0/2 grid.

## Causal dependency

**A:** Find original four-neighbor singleton red islands and erase them.
**Intermediate:** The resulting zero-component partition, newly joined cells
and region areas.
**B:** Classify each recomputed enclosed region by the canonical thresholds.

An X in a 5×5 interior has four zero regions of area 4. Erasing its five
eligible red cells joins them into a region of area 21. Consequently all sixteen
original zero cells change from the skip-A rule's cyan to yellow. The four red
corner cells remain attached to the frame. This is a change in connectivity and
area, not a pointwise recoloring of the erased cells. The source-bound protected
Racket witness is returned under `checks/b28619e32f6f/causal/`.

## Reproduce from the packet's outer directory

Use its passing Python interpreter and bundled Racket setup. Payload paths are
relative to `WORK/repo`.

```sh
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/b28619e32f6f/tests
WORK/.venv/bin/python review.py run python3 \
  generators/b28619e32f6f/workspace/parametric/audit.py \
  --out generators/b28619e32f6f/workspace/parametric/evidence/fresh-audit
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  b28619e32f6f --out ../checks/b28619e32f6f/fresh-qualification --summary
```

Choose new output paths. The reusable `audit.py` checks the canonical input
grammar, matched input streams, count/query-prefix boundaries, sixteen explicit
shortcut rules, actual Racket labels, private-field invariance and malformed
public grids. Its current bounded run covers 144 episodes, 32 Racket labels and
32 setting/rival checks; detailed limits and programs are retained in
`evidence/current/audit.json`. Equivalent aliases under `keep` are reported as
survivors with matching query predictions, not falsely counted as defeated.
There is no uniqueness claim beyond this finite set and no measured learning
benefit claim.

## Public/private projection

`evidence/current/examples.private.json` keeps one two-demo/four-query episode
per setting, with all labels and programs, exclusively for the controller and
reviewer. Each hash-named file in `evidence/current/public/` contains only the
demos and the **first** query input. Its identifier hashes exactly those visible
bytes. Changing private settings, seed, program or answers leaves that ID
unchanged; the first turn equals the one-query generation projection.

The existing consumer must retain the other three queries privately and reveal
one after each preceding response, with no total-count or final-turn hints.
Do not give `examples.private.json`, the audit programs, qualification execution
records or causal witness to a model answering a public challenge. No training
loop or turn controller is introduced here.

## Inherited finding and acceptance boundary

The old canonical sampler's missing equality-boundary support remains an open
source-bound finding in `evidence/review_index.json`. This adapter repairs that
teaching support within its own generation path; it does not resolve the
unchanged canonical sampler's audit or refresh its approval hashes.

The inherited root-level canonical test uses obsolete paths/imports, and the
frozen return scope forbids modifying it. A portable canonical regression copy
is supplied in `tests/test_canonical_portable.py`; all 27 tests in that allowed
directory pass. The whole-home legacy task-runner preflight remains blocked on
the unchanged root-level test and needs an owner-side portability repair.

The reviewer supplies source inventory, native qualification and the replayed
causal witness. The owner must integrate, qualify and accept the exact live
source before production parametric export. No training activation is implied.
