# Native phase-anchor family

This proposed family preserves the source puzzle's wall-partitioned chamber
reasoning. It changes only how a multi-color chamber chooses the checkerboard
phase. The production generator, canonical authority, and production approval
are unchanged. Reviewer qualification is evidence for owner intake; it is not
owner acceptance or training admission.

## Rule parameter

| `phase_anchor` | Meaning |
|---|---|
| `bbox_top_left` | Canonical rule: the chamber bounding-box top-left cell receives the numeric minimum marker color. |
| `minimum_marker` | Select the input coordinate carrying the chamber's numeric minimum marker color; that coordinate receives the minimum color in the completed checkerboard. |

The default `{"phase_anchor":"bbox_top_left"}` returns the selected canonical
Racket program byte-for-byte. Both settings discover the same 4-connected
non-wall regions, collect distinct nonzero marker colors, fill singleton-color
regions solidly, ignore a third middle color during a checker fill, and alternate
the numeric minimum and maximum colors.

The alternative has a real two-step dependency. **A** identifies each
multi-color region's numeric minimum marker and its input coordinate. The
coordinate is the input-dependent intermediate. **B** uses that coordinate as
the checker phase origin. B cannot choose which parity receives the minimum
color until A returns that coordinate. The retained wrong-intermediate witness
substitutes the maximum-color marker coordinate and changes the final grid under
protected Racket.

## Sampling and teaching

`generate(seed, settings, demos=3, queries=4)` supports **2–6 demonstrations**
and independently **1–4 queries**. Normal use has four queries, revealed one at
a time. The sampler builds one deterministic six-demo/four-query plan without
consulting the setting, then returns prefixes. Therefore settings receive exact
matched inputs and the first turn of a four-query episode is byte-identical to a
direct one-query request.

The first two demonstrations jointly reject the other declared setting and
these executable finite rivals: maximum-marker anchoring, row-major first/last
marker anchoring, global-origin anchoring, a one-cell flipped canonical phase,
minimum-value-parity anchoring, using the two smallest colors, and solid minimum
fill. This is a finite teaching guarantee, not uniqueness against every program.

Four query profiles are **9×11, 15×17, 23×27, and 30×30**. They vary lattice
shape, chamber sizes, palettes, singleton/two-color/three-color regions, marker
orders and parities, and isolated wall blockers. The 30×30 query uses four
chamber rows and columns with one seven-cell chamber dimension; this is a
separate parametric grammar extension beyond the unchanged production
validator's six-cell chamber maximum, not padding.

## Public/controller separation

The adapter returns a private authoring object containing all query labels,
settings-derived program source, and sampling metadata. Public evidence uses
`reviewer_support.public_challenge_bytes` with exactly two visible demonstrations
and only the first query input. Settings, seed, program, query answers, and
future query inputs are absent. Files under `evidence/native-v1/public/` are
named by the SHA-256 of those exact bytes. Complete episodes, rival programs and
causal metadata stay under `private/`.

## Reproduce from the packet outer directory

Use a passing interpreter from `review.py python-check`. Choose new output paths
for audit and qualification artifacts.

```sh
python3 review.py run python3 -m pytest -q \
  generators/f1c8ea826b10/tests/test_native_parametric.py

python3 review.py task-tests f1c8ea826b10 --phase after \
  --out ../checks/f1c8ea826b10-tests

python3 review.py run python3 \
  generators/f1c8ea826b10/workspace/parametric/audit_native.py \
  --out generators/f1c8ea826b10/workspace/parametric/evidence/new-audit

python3 review.py run python3 -m arcpuzzles parametric qualify f1c8ea826b10 \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/f1c8ea826b10/qualification --summary
```

The owner must integrate these exact bytes, re-run native qualification, inspect
the parameter semantics and grammar, and explicitly accept the family. Any
source change invalidates prior qualification. No artifact here admits data to
training or changes allocation weights.
