# Proposed odd-gap ownership variants

Task `613be474907a`, original training parent `d968ffd4`. This executable prototype
keeps the two solid colored blocks, unique modal background, bounding-box reasoning,
horizontal-before-vertical branch precedence, and full perpendicular-line painting.
Each block extends through `floor(gap / 2)` lines. One episode-fixed rule parameter
controls the remaining middle line when the gap is odd:

| `center` | Remaining line | Status |
|---|---|---|
| `preserve` | Original background | Exact canonical program, rule hash `adc52fde010d` |
| `near` | Left block's color, or top block's color for vertical separation | Proposed variant |
| `far` | Right block's color, or bottom block's color for vertical separation | Proposed variant |

Even-gap behavior is identical for all settings. Near/far are spatial roles, not
numeric color order. The parameter changes execution, and input sampling uses
only the seed and geometry controls. Original generator/rule/approvals are unchanged.

## Run from the outer extracted packet

Python 3.12+, the packet's NumPy/Pillow runtime dependencies, and its included
Racket runtime are sufficient for authoring; pytest is needed for the tests.

```sh
python3 review.py setup
python3 review.py run python3 generators/613be474907a/workspace/parametric/prototype.py --seed 17 --center all --train 4 --test 4 --out ../checks/bridge-variants
python3 review.py run python3 generators/613be474907a/workspace/parametric/prototype.py --seed 73 --center all --train 2 --test 4 --height 30 --width 30 --out ../checks/bridge-large
python3 review.py run python3 -m pytest -q generators/613be474907a/tests/test_parametric_bridge.py
```

Both the Python API and CLI default to the canonical `preserve` setting.
Output directories must be new. `--center` accepts `preserve`, `near`, `far`, or
`all`; `all` writes three complete episodes. `--train` accepts 2..32 and `--test`
accepts 1..32 independently. Optional exact `--height` / `--width` accept 7..30.
A bounded sampler raises if uniqueness fails; it never truncates the request.

The minimum two demonstrations include horizontal and vertical odd-gap cases,
reversed numeric color order, and a diagonal case exposing horizontal precedence.
The default four-query schedule includes an exact 30x30 case and substantial gaps,
while default demonstrations are smaller. Fixed-size modes exercise both axes,
both parities, and palette changes. Every input is distinct within its episode.

## Evidence and visibility

Every emitted label is executed with the matching Racket program through the
included protected bridge; Python is a cross-check and rival implementation.
The canonical default also agrees with all five distinct canonical examples in
the focused tests. Programs, seeds, settings, source hashes, query answers,
reference-runtime identity, and per-query teaching results live in `private/`.

Give solvers **only `public/`**. Its filenames are the SHA-256 hashes of the exact
visible bytes written: demonstration inputs/outputs and query inputs. Filenames
contain no seed, parameter, or setting ordinal. Changing a query answer or private
metadata cannot change the visible bytes or public ID. Batch files are ordered by
public ID and duplicate visible payloads are rejected before writing.

Teaching checks select all three parameter hypotheses using demonstration pairs
only. They also check identity, horizontal-only, vertical-only, vertical-first,
bounded-span painting, and lower-color-on-near-side shortcuts. For each query,
all surviving predictions must agree. The negative regression retains all three
settings after even-gap-only demonstrations and rejects identifiability of an
odd-gap query. These checks cover a finite declared rival set, not every possible
rule or model learning. Query answers never select or eliminate rivals.

This prototype does not establish production integration, new source approval,
training admission, or corpus-wide size/query support. Its sampler supports
7..30 dimensions; smaller lawful canonical grids are checked as canonical anchors,
not advertised as prototype size overrides. The canonical scope is unchanged.
