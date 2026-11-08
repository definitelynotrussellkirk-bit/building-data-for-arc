# 9d2f7c9e2ac4 — current generator decisions

## Rule and scope

The unchanged canonical Racket rule (`3d50e1ec984b`) rotates the occupied BL
bounding box clockwise into BR, preserving the BL bounding-box row/column
offsets and source color. It preserves every other pixel. The maroon cross is
fixed color 9 and background is 0. Racket chooses the transformation directly;
it does not infer a variable transformation from the upper example.

Version 3.0.0 generates the complete TL/TR worked example, a connected
monochromatic BL source, and an empty BR target, with a unique centered cross
on a 9..15 square grid. Every rotation fits. Its input domain intentionally
excludes the authority's clipping, disconnected-source, multicolor-source,
missing-cross and BR-overlay edge behavior.

## Reversals and current controls

Version 2.1.0 omitted both upper objects, generated only three total colors,
and silently ignored most of its eight advertised controls. It also accepted
malformed context and restricted valid grid-size overrides by difficulty.
The retained before source is
`472557d4c9af8f435e6c2655e3568c44cc2c8b85a1de23c7f55ed304bd040113`.
The repair restores the upper example and replaces decorative metadata with
five exact pixel-observable controls:

| Control | Exact meaning |
|---|---|
| `grid_n` | Square size 9..15, valid in every difficulty band |
| `shape_variant` | 0/1/2 selects exactly 4/5/6 BL cells |
| `example_color` | TL/TR color 1..8 |
| `source_color` | BL and copied result color 1..8 |
| `source_position` | `origin/down/right/diagonal`: BL bbox offsets (0,0)/(1,0)/(0,1)/(1,1) |

The old `palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`,
`density` and `texture` names are retired and fail loudly. `shape_variant`
now has an explicit cardinality contract. `None` means no override. Invalid
numeric coercions and unknown names raise ValueError. All declared joint
combinations fit constructively, including equal explicit object colors;
unforced production always has two distinct object colors.

## Teaching distribution

The finite connected asymmetric 3x3 shape banks contain 8, 16 and 32 oriented
4/5/6-cell shapes. Geometry is cached, not complete examples. Each default
source distinguishes the eight D4 transformations and differs from the upper
example's normalized shape. Symmetric canonical examples remain valid inputs;
source asymmetry is a generation preference, not a validator restriction.

Source offsets cycle through four positions, with three demonstrations and one
query. Every ordinary consecutive four-pair window has two row-shift witnesses,
two column-shift witnesses, two unequal-offset witnesses, two color-rank
contrasts and two deliberate upper/source offset contrasts. The remaining
upper placements are randomized. This redundancy survives every one-pair query
holdout. The lesson hook scores the actual labels against 17 named rivals.

`counterexamples/offset_and_color_witnesses.json` contains four real production
pairs with actual Racket labels, exact seeds/accepted indices and source hashes.
Eight declared shortcuts fit all three canonical labels; these pairs distinguish
offset resetting/swapping, template-row reuse and maximum-color copying.
`counterexamples/baseline_missing_context.json` retains the old accepted input
with both upper example objects absent.

## Verification and limits

For source `8105b0c6704d022567a9681768c76fc3624d3be5c300b1b941a9fbc1494cf104`:
all 12 after-check stages passed, including required query rotations; all 88
portable regression cases passed. The override matrix accepted 34,380/34,380
draws across 382 cases, with no findings or warnings. All three canonical
inputs are accepted; 47/60 profile-floor draws match a canonical size/palette
profile (easy 17/20, medium 15/20, hard 15/20).

The actual production census materialized 300 lessons, 1,200 pairs and 1,200
query rotations: zero declared-rival ambiguity or hook/scoring errors, with
1,194 unique inputs. This is finite evidence against declared rivals, not
universal identifiability. Arbitrary downstream filters that remove schedule
phases can break the teaching guarantee; retain accepted indices and recheck
lessons after such filtering. Centered-split, rarest-foreground-color source
selection, empty-target clearing and no-clipping alternatives remain
answer-equivalent on this bounded generated domain. No broader coverage or
training admission is claimed.

No earlier current review index was present in this packet. This return repairs
its selected generator only; its two drawn audit targets retain separate,
source-bound findings for maintainer triage.
## Current reviewer considerations

Source SHA-256: `8105b0c6704d022567a9681768c76fc3624d3be5c300b1b941a9fbc1494cf104`.

# Decisions — 9d2f7c9e2ac4, version 3.0.0

## D1 — Restore the input's worked analogy

The old sampler emitted only the cross and bottom-left source. Its canonical
reference inputs also contain a top-left shape and its top-right clockwise
rotation. No historical justification for omitting both upper objects was
present. Restore those objects, independently vary the upper orientation,
placement and color, and ensure the upper normalized shape differs from the
source. This removes the missing-context defect without changing the rule.
The actual Racket authority ignores the top pair and always performs clockwise
rotation; a variable analogy transformation would require a different rule and
is outside this repair.

Evidence: baseline battery, `checks/baseline-missing-context.json`, all three
canonical pairs checked by `tests/test_rotation_contract.py`, actual Racket
probes in `checks/rival-investigation/`, and the final after battery.

## D2 — Make the controls true statements about pixels

Expose exactly `grid_n`, `shape_variant`, `example_color`, `source_color`, and
`source_position`; `observe_overrides` recovers each from an independently
constructed grid. The six obsolete palette/count/density/position/texture names
are rejected instead of silently ignored. Version 3.0.0 marks that control
migration. `shape_variant` now means source cardinalities 4, 5 and 6.

Every integer grid size 9..15 is valid in every difficulty. Difficulty changes
sampling weights, never override validity. Invalid integers, coercible strings,
floats, booleans and unknown names raise ValueError. `None` preserves defaults.
Equal explicit object colors are legal and honored; ordinary production chooses
different colors so canonical four-color scenes are represented.

Rejected alternatives: keeping singleton axes as decorative metadata, silently
clamping counts or grid dimensions, and retaining invalid diagnostic textures
inside the ordinary input domain. The original reasons for the inert controls
are unknown. Final matrix: 382 cases, 34,380 draws, all accepted exactly; no
findings, warnings or hidden incompatibilities.

## D3 — Construct shapes and placements instead of reducing failed requests

Enumerate the connected, fully asymmetric 4/5/6-cell shapes within a 3x3 box:
8/16/32 oriented shapes. Draw from immutable geometry banks and vary positions,
colors, sizes and upper examples. Every source and its rotation fit when either
bbox offset is 0 or 1, including the smallest/even 9x9 and 10x10 canvases.
There are no placement retries or short fallback shapes. Canonical sources with
reflection symmetry remain validator-accepted.

The alternative of completely unrestricted small polyomino draws can produce
three symmetric demonstrations and an asymmetric query, hiding a wrong
orientation rule until the query. Every generated source now distinguishes D4
alternatives. The cost is explicit: generated source cardinalities are only
4..6 and bounding boxes at most 3x3, even on larger grids. Rarest-foreground-color
source selection remains equivalent on these defaults because the four-cell
upper shape occurs twice. That is a known domain limit, not a claimed refuted
rival or evidence about a broader task population.

## D4 — Teach offsets and color roles with redundant evidence

Keep three demonstrations plus one query. Source offsets cycle through origin,
down, right and diagonal. Two of each four scenes distinguish row shifts, two
column shifts, two swapped offsets, and two source-vs-template row choices.
Source/example numeric rank alternates. Upper placements in the other phases
remain random to avoid enforcing a single global complement relationship.

There are 17 distinct named rival rules. Eight fit all three canonical labels
and require generated counterexamples. The final 300-lesson Racket census
retains every accepted index and exact label: 1,200 pairs, 1,194 unique inputs,
no rejection, zero ambiguous production lessons, and zero ambiguous outcomes
across all 1,200 query rotations. Production is three demos in sampled order;
rotations hold out each of the four labeled pairs once and preserve the other
three in order. The extra fixed-seed schedule receipt enumerates the four
cyclic starts in each band. See `checks/schedule-census.json`.

Independent review enumerated 320 four-scene windows and 1,280 holdouts against
an independent Python oracle, with no findings. Its deliberate downstream
filtering negative removes needed phases and correctly triggers the lesson
hook. These are different populations and authority bases; their counts are not
pooled. Finite evidence against named rivals does not prove universal induction.
Recheck lessons if downstream filtering, assembly or explicit overrides change.

## D5 — Preserve the authority and narrow validator assumptions explicitly

The Racket rule and canonical ledger are unchanged. Actual authority probes
confirm its wider behavior: clipping, first-source-color repainting, disconnected
aggregate rotation, empty-source identity and BR overlay. Those are excluded
from the intended generator domain. `self_check` validates all three occupied
panels, the complete centered cross, an empty target and full target fit, and
returns reasons on malformed grids. Strict canonical support additionally
requires size 9 or 11 and two distinct object colors.

No canonical profile opt-out or semantic exemption was used. The independent
profile check improved from 0/60 to 47/60 exact size/palette hits; all three
canonical inputs remain accepted. No earlier current audit index was present.

## D6 — Preserve failed attempts and make the result portable

Retain the baseline's four failing stages, 77 failed regression cases, and the
isolated task-test prerequisite failure. Resolve the last by creating a new venv
from cached wheels, without disabling user-site isolation or altering the host.
The offline bootstrap and outer-layout-aware patch replay scripts are optional
shared-tool proposals under `checks/tooling/`, outside the selected source patch.

Both assigned audits are findings-only. Each has exact source identities,
minimal reproduction, actual Racket evidence and its own section in `AUDIT.md`.
Both solve episodes retain their genuine single attempt and exposure declarations.
Each passed 3/3 visible examples; private-query correctness is unknown and no
training admission is claimed. Final patch replay is recorded separately in
`checks/replay-final/` and the top-level `RESULTS.json`.

## Native parametric extension — rotate, then derive a cue

`workspace/parametric/` adds a finite two-setting lesson without changing the
catalog default. `copy_only` returns the canonical Racket source byte-for-byte.
`cue_payload` first executes that same BL-to-BR clockwise rotation, then finds
the unique cue color adjacent to the newly painted BR object and recolors all
remote payloads of that derived color with the source color. The second stage
therefore consumes an input-dependent intermediate rather than a setting-only
constant.

Both settings receive identical inputs. Lessons contain 2–6 demonstrations and
exactly four novel queries; each query set contains a substantive 30×30 case.
The bounded task-local audit covers seeds 0–31 at demo counts 2, 3, and 6 and
rejects fixed-lowest-cue and no-postprocess rivals from visible demonstrations.
That audit is finite Python-mirror evidence only. Protected-Racket execution,
source binding, sole-survivor teaching checks, and causal ablation are recorded
separately by native qualification and witness receipts; no owner acceptance or
training admission is claimed here.
