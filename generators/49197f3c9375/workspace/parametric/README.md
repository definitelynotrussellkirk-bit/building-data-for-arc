# Unmatched shape: boundary, whole, or interior

This is a separate native prototype for `49197f3c9375`. The production generator
remains version `3.0.0` with its selected canonical authority and approval bytes.
The default program is the exact selected Racket source, stored in `canonical.rkt`.
Owner qualification and fresh acceptance are still required after integration.

## Rule and causal dependency

First extract nonzero monochrome four-connected components. Normalize their
complete shapes under all eight rotations/reflections and find the sole D4
shape class occurring once. The selected component's cells, color and original
bounding box are the intermediate consumed by the rendering step.

| Private episode setting | Rendered cells |
|---|---|
| `{"render":"boundary"}` (canonical default) | Selected cells with at least one missing four-neighbor |
| `{"render":"whole"}` | Every selected cell |
| `{"render":"interior"}` | Selected cells with all four neighbors present |

All settings preserve the selected component's original bounding box and color.
Boundary includes edges beside internal holes. A thin object's interior is an
all-zero grid of the original dimensions; it is not cropped away. The Racket
variants use guarded replacements at unique canonical sites. The Python mirror
reuses the reviewed component/signature helpers and is checked against protected
Racket, rather than treated as label authority.

## Supported input and episode contracts

Inputs are exact-integer ARC matrices, 8..30 rows by 15..30 columns, with zero
background. They contain 5, 7 or 9 monochrome four-connected components: one
full-D4 signature occurs once and all other signatures occur twice. Target area
and bounding-box dimensions, allowing transpose, must each be shared by another
component. The constructive sampler strengthens this to a single other component
sharing both properties and keeps objects separated by background.

`adapter.generate(seed, settings=None, demos=3, queries=4)` accepts exact integer
seeds in `0..2**63-1`, independently selected demo counts in `3..6`, and query
counts in `1..4`. Booleans, coerced numbers, unknown settings and out-of-range
requests fail explicitly. An omitted setting selects `MODES[seed % 3]` once for
the episode. Every setting shares the same input bank for a seed. Complete
six-demo/four-query banks use per-role SHA-256-derived local random streams
before slicing, preserving prefixes, fresh outputs and global RNG state.

The mandatory three demonstrations place the target middle, first and last,
with distinct, reused and monochrome palettes. They teach an asymmetric thick
hollow shape, a scaled hollow ring, and an explicitly thin control. Thick/hollow paired
distractors prevent unique topology from directly selecting the target. Chiral
pairs provide rotation-only and reflection-only relations. Additional demos add
paired classes and other topologies. Four queries use 5/7/9/9 objects; the first
is 8x15 and the last two are 30x30 with nine actual 8x8, area-48 components spread
near all edges. Three query targets have interiors; one tests the empty branch.

The sampler uses a finite literal bank of eight connected shape templates and
varies orientation, pairing, palette, placement, scale, canvas and object count.
It does not claim coverage of every connected polyomino or arbitrary topology.

## Run and reuse

From the extracted packet's outer directory, payload paths are relative to
`WORK/repo`. Choose new output and receipt paths for each run:

```sh
WORK/.venv/bin/python review.py run --receipt checks/49197f3c9375/recheck.json \
  python3 -m pytest generators/49197f3c9375/tests/test_native_family.py \
  generators/49197f3c9375/tests/test_native_sampler.py \
  generators/49197f3c9375/tests/test_native_adapter.py -q

WORK/.venv/bin/python review.py run --receipt checks/49197f3c9375/rival-recheck.json \
  python3 generators/49197f3c9375/workspace/parametric/audit.py \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/49197f3c9375/rival-recheck

WORK/.venv/bin/python review.py run --receipt checks/49197f3c9375/requalify.json \
  python3 -m arcpuzzles parametric qualify 49197f3c9375 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/49197f3c9375/requalification --summary
```

The generic adjacent `audit.py` reads the adapter/promotion contract and
`native_family.rivals`. It accepts integer canonical grids or digit-string rows,
including a canonical test dictionary. It caches exact protected executions,
records source hashes, and separates demo refutations, query conflicts, lawful
finite consistency, and execution errors. It never uses query answers to choose
a rule. Audit programs and labeled episodes are private evidence.

The packet's `boundary_probe.py` checks the maximum seed and 6+4 request through
Racket, records actual input occupancy/span/boundary contact, and handles both occupied and empty outputs. Its required `--out NEW.json` refuses overwriting prior evidence. `public_probe.py` verifies
the native saved projection and three corrupted copies: leaked query answer,
orphan public file, and missing public view. It does not claim another Racket
replay. Both helpers are standalone task-scoped copies with no predecessor
checkout dependency.

## Evidence and limits

Independent review found five feature-selection shortcuts fitting the original
three demonstrations and disagreeing on queries: exposed-edge perimeter,
perimeter plus interior count, D4 orbit size, projection histograms, and minimum
D4 orbit size. Sixteen seed/setting cases were confirmed through protected
Racket and retained with frozen baseline sources. The repaired first demo uses
distinct full shapes sharing perimeter, interior count, orbit size and projection
histograms, plus a more symmetric distractor. Its non-first target and distinct
colors make erroneous selection observably wrong. The second target moves to
first position, and the third thin example remains. The lesson still uses three
demonstrations; all four query roles are preserved. These exact rival programs
are now part of the reusable audit menu.

The first repair exposed a rotation-only grouping shortcut for interior lessons.
The final first demo therefore uses a reflection-only chiral pair and guarantees
that one member precedes the true middle target. This supplies an observable
wrong intermediate for the shortcut while preserving the existing query streams.
The failed intermediate audit and focused RED/GREEN regression are retained.

The source-bound evidence inventory records only the retained focused checks.
The finite rival menu includes positional, size, bbox, color, translation-only,
rotation-only, boundary-before-grouping and rendering shortcuts. Passing this
menu is not a proof of unique induction over all programs. The preserved native
qualification supplies full three-demo/four-query examples for every setting.
The causal witness executes a wrong selected-component intermediate and requires
a changed final label. Public views contain demonstrations and one current query
input only; settings, programs, answers and future queries remain private.

These checks establish reviewer readiness for the exact returned source.
They do not grant owner acceptance, training admission, or measured learning
benefit. No production battery was rerun for this separate prototype-only change.
