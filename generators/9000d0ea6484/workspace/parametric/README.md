# Native panel-priority family

This directory extends the retained eight-scan prototype with input-derived
starting sections, independent demonstration/query counts and a strict public
export audit. The production generator and exact canonical Racket rule remain
unchanged. Reviewer qualification is separate from owner acceptance and training.

## Episode rule

| Parameter | Values | Canonical default |
|---|---|---|
| `start_section` | `0`, `1`, `2`, `3`, `densest`, `sparsest` | `2` |
| `scan_direction` | `forward`, `reverse` | `forward` |

Integer starts reuse all eight guarded programs from `prototype.py`.
The canonical default is byte-exact, SHA-256
`3bec9ede53940dce7bdf0aa83666b99ea3fb754cb6c4d356406e7eab30dade8c`.

For a density start, count nonzero cells separately in each panel. Select the
largest or smallest count, resolving ties in section order `2,3,0,1`. Then
scan cyclically from that selected section, adding or subtracting one modulo
four according to the fixed direction. Each aligned output cell takes the
first nonzero value in that scan, or zero when every source is empty.
Empty panels participate and may win `sparsest`. The input-dependent count
vector is needed before the scan can be chosen.

## Input and request contracts

The API admits literal list-of-lists grids with 1–30 rows and exactly 19 columns.
Columns 4, 9 and 14 are full-height color-3 dividers. Other cells use integer
colors `0,1,2,4,5,6,7,8,9`. It rejects bools, floats, tuple rows, ragged grids
and malformed dividers. Payloads may contain multiple colors or empty panels.

Generated panels each use one distinct nonzero color. Every generated grid
contains empty, four solo and all six pairwise aligned signatures, requiring
at least three rows. Maximum substantive stress is 30×19. Exact 30×30 would
add eleven columns ignored by the unchanged canonical rule and is not claimed.
Global rotations are outside this horizontal-panel grammar; aligned local
panel transforms are sampler variations.

`generate(seed, settings=None, demos=4, queries=4)` requires exact integer seeds
in `0..2**63-1`, 4–6 demonstrations and 1–4 queries, independently.
Omitted settings choose `SETTINGS[seed % 12]`; request the explicit canonical
setting for canonical behavior. Input sampling is independent of settings.
A complete six-demo/four-query bank is built before slicing, preserving prefixes
and the first query. All ten bank inputs are distinct.

## Four-demo teaching design

The first demonstration has panel counts `[9,4,7,6]`. All panels occupy four
rows and four columns, while four-neighbor component counts are `[1,4,3,4]`.
These distinguish cell count from row, column and component selectors.
The next demonstrations use `[5,5,9,9]` and `[5,9,5,9]` to teach extreme ties.
A fourth gives section 1 the unique largest count and section 3 the unique
smallest count. All four panels therefore win during the teaching prefix.
Three global-anchor demonstrations left a plausible ignored-candidate shortcut;
the repair costs one additional example rather than removing query branches.
Complete pairwise overlaps expose wrong scan orders and missing fallbacks.
Palettes break numeric and fixed canonical color shortcuts.

The audit compares all declared settings and named executable alternatives
using only demonstrations, then checks four queries. It retains exact programs
and counterexamples. This is finite evidence, not universal uniqueness or a
measurement of learning benefit.

## Replay from the packet's outer directory

Use the ready Python chosen by `review.py python-check`:

```bash
WORK/.venv/bin/python review.py run python3 -B -m pytest -q \
  generators/9000d0ea6484/tests/test_native_adapter.py \
  generators/9000d0ea6484/tests/test_native_audit.py

WORK/.venv/bin/python review.py run python3 -B \
  generators/9000d0ea6484/workspace/parametric/audit.py \
  --out ../checks/9000d0ea6484/audit-new

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  9000d0ea6484 --seed 0 --seed 17 --demos 4 --queries 4 \
  --out ../checks/9000d0ea6484/qualification-new --summary
```

Output directories must be new. Refresh the native source/evidence manifest
after code changes, supplying its exact old hash to the replacement guard.
Current task notes and packet `REVIEW.md` identify executed receipts; commands
above are replay instructions.

## Public/private boundary

`public_turn(episode, index)` exposes demonstrations and one input-only query.
It omits settings, seed, programs, query answers, future inputs and count hints.
The first visible turn is identical for matched single- and four-query requests.
Protected Racket must verify the native Python claims before publication.

The audit writes separate private evidence and public files named by their
visible content hashes. Its verifier checks exact bytes, strict grids, IDs,
counts, references and projections, rejecting altered or orphan files.
Serialized checks do not authenticate a wholesale adversarial rewrite and do
not substitute for protected execution, owner acceptance or training admission.

## Retained legacy authoring evidence

`prototype.py` and `evidence/final/` retain earlier evidence for eight fixed
scans. Its old writer emits 3+1 examples with seed-bearing filenames; it is
not the native four-query/public-ID exporter. The native adapter reuses only
its fixed-rule materializer, never its nested-Racket episode builder.
Historical receipts do not certify the new native source.
