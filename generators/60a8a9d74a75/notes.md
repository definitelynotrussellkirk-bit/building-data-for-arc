# Working notes: 60a8a9d74a75

## Current rule and authority

For each 4-connected zero component, collect its cardinally adjacent colors after
ignoring 0 and 8. Fill the whole component exactly when that distinct color set
has size one; otherwise leave it unchanged. The selected Racket authority remains
semantically unchanged and is pinned by `RULE_HASH = "49411595dc9e"`.

The selected bank record had a stale comment in `target_code`; it was synchronized
byte-for-byte with its already identical `raw_code`. This was comment-only and did
not alter executable behavior.

## Current generator: v3.1.0

The previous frame-only random sampler was replaced by a deterministic four-profile
schedule:

1. `canonical_rows` — two color-8 chambers, one seed each.
2. `composite_open_left` — four regions exercising hidden branches.
3. `canonical_cols` — the transposed canonical chamber idiom.
4. `composite_open_top` — rotated composite evidence.

Every ordinary four-pair lesson therefore contains two canonical and two composite
pairs. Three demonstrations are required. `lesson_identifiable` requires those
three demonstrations to refute every declared rival even when any one pair is the
query.

Composite inputs contain exactly four zero regions: repeated same-color seeds
(positive), two different neighboring colors (negative), one edge-connected
single-color region (positive), and one region bounded directly by a non-8 color
(positive). The only advertised exact override is `profile`; unknown or malformed
overrides fail closed.

## Reversed choices and evidence

- **Prior choice:** loosely randomized frame geometry with dead/clamped axes.
  **New choice:** four explicit semantic profiles and one observable exact axis.
  **Reason:** the baseline battery was 6 green / 2 advisory / 4 failed and reported
  tens of thousands of override mismatches plus no teaching contract.
- **Intermediate choice:** allow repeated seeds anywhere inside the composite
  chamber. **New choice:** keep them one cell away from the chamber boundary.
  **Reason:** seeds `(2,37)` and `(6,105)` pinched off a corner zero cell, creating
  an unintended fifth component; focused regressions now retain both cases.
- **Intermediate choice:** smaller composite regions. **New choice:** a 17×22 base
  plus difficulty-dependent padding. **Reason:** the first after battery missed the
  canonical object-size envelope; the enlarged geometry passes profile floor.

## Strongest known shortcut

`single_seed_8_chambers`: fill only enclosed 8-walled regions touched by exactly
one colored cell. It fits all five canonical pairs. The retained generated witness
is seed 901, sample index 1, difficulty hard, profile `composite_open_left` in
`counterexamples/single_seed_8_chambers.json`; the intended rule changes 151 cells
while this rival leaves the input unchanged. The independent probe and Racket
receipt are under `checks/shortcut-witness*`.

## Validation and limits

Final generator SHA-256:
`570fc941da7e0efc5efbee58d5b49f8173a062b6c2966201d8bf7c02a92dcc73`.

Final evidence: 12/12 battery stages green, 42/42 focused portable tests, 600/600
semantic draws without crashes, 400/400 independent probe draws accepted, and a
300-lesson / 1,200-query-rotation census with no declared-rival ambiguity or
scoring errors. Finite rivals do not prove unique induction against every possible
program. Catalog training approval remains outside this review and is still false.

No prior return was used as a factual measurement; the selected immutable baseline
and current-source checks were used directly. Imported associated notes were empty.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.
## Current reviewer considerations

Source SHA-256: `570fc941da7e0efc5efbee58d5b49f8173a062b6c2966201d8bf7c02a92dcc73`.

# Decisions for 60a8a9d74a75

## D1 — Keep the canonical rule; synchronize only selected-record text

**Original state.** `raw_code` and `target_code` implemented the same zero-component
rule, but `target_code` contained a stale misleading comment. The authority-sync
stage failed exact comparison.

**Decision.** Preserve executable Racket behavior and remove only the comment so the
two selected fields are byte-identical. Keep `RULE_HASH = "49411595dc9e"`.

**Alternatives rejected.** Rewriting the Racket program was unnecessary and would
have increased authority risk. Leaving the comment divergence would keep the final
battery red despite semantic parity.

**Probe and failure mode.** Canonical-pair tests and the Racket rule-smoke stage bind
outputs; authority-sync now reports synchronized exact, whitespace-normalized, and
comment-stripped groups. A future semantic edit must update the pin and rerun those
checks.

## D2 — Replace broad random frames with four explicit semantic profiles

**Original state.** The sampler varied frame geometry but mostly generated the same
single-seed enclosed behavior. This made many parameters nominal rather than
observable and failed to teach edge contact, repeated same-color neighbors, mixed
colors, or colored boundaries.

**Decision.** Use a deterministic period-four schedule:
`canonical_rows`, `composite_open_left`, `canonical_cols`,
`composite_open_top`. Canonical profiles maintain direct support; composites cover
all hidden branches in one input.

**Alternatives rejected.** Pure rejection sampling over arbitrary grids was harder
to validate, less reproducible, and could silently omit rare branches. A curriculum
of only composite cases would lose the canonical idiom. Random profile selection
would not guarantee evidence in every four-pair lesson.

**Probe and failure mode.** The independent 400-draw probe checks profile counts,
changed-cell range, region sizes, and rival disagreements. Exact profile overrides
are exercised across all bands. The domain remains intentionally narrower than all
lawful rule inputs.

## D3 — Expose only the exact `profile` axis

**Original state.** `grid_h`, `grid_w`, and `position_bias` were clamped, ignored, or
single-token controls; unknown keys were accepted. The baseline override checker
reported tens of thousands of mismatches.

**Decision.** Remove dishonest controls. Advertise one categorical axis whose value
can be reconstructed from the output grid; reject unknown keys and malformed values.

**Alternatives rejected.** Keeping approximate size axes would violate the exact
override contract. Adding many low-value knobs would expand the test matrix without
improving semantic coverage.

**Probe and failure mode.** The final override report accepts 450/450 planned draws
and records zero findings. `observe_overrides` fails if a generated grid is not one
of the exact declared profiles.

## D4 — Validate two explicit manifolds, not “anything with zeros”

**Decision.** `self_check` accepts either the canonical two-chamber grammar or a
composite with exactly four semantic regions. It rejects ragged grids, booleans,
out-of-range colors, destructive mutations, missing branches, extra components, and
incorrect edge orientation.

**Reversed intermediate choices.** Initial composite seeds were allowed next to the
wall. Two retained draws pinched off a corner zero into a fifth component; seeds now
stay one cell inside. The initial composite base was also too small for the profile
floor; it was enlarged to 17×22 plus difficulty-dependent bottom/right padding.

**Probe and failure mode.** Retained focused tests cover both exact corner-pinch
seeds, scale, malformed inputs, and destructive mutations. The validator is stricter
than the mathematical rule domain by design; this is documented, not hidden.

## D5 — Make teaching identifiability executable

**Decision.** Declare four canonical-fitting rivals:
`single_seed_8_chambers`, `exactly_one_colored_cell`, `enclosed_only`, and
`first_color_wins`. Declare a witness for each hidden branch and require three
demonstrations to refute every rival.

**Ordering/query policy.** A lesson uses four consecutive scheduled pairs: three
demonstrations and one query. Any pair may be held out. With two composite profiles
per period, every cyclic query rotation retains at least one composite demonstration.

**Alternatives rejected.** Correct labels alone were insufficient because canonical
pairs do not distinguish the rivals. Requiring a fixed query position would create
an unnecessary downstream ordering dependency.

**Probe and limitation.** Focused tests enumerate cyclic schedule starts and all
query positions. The source-bound census checks 300 production lessons and 1,200
rotations. These checks cover declared rivals only; they do not prove universal
identifiability.

## D6 — Retain an independent probe and exact shortcut witness

**Decision.** Add `workspace/reference_probe.py`, which independently recomputes
zero regions and labels instead of calling the production mirror. It dynamically
iterates the generator's declared competitors. Retain seed 901/sample 1/profile
`composite_open_left` as the minimal source-bound shortcut witness.

**Reason.** A second implementation catches shared assumptions, gives future agents
a reusable scan tool, and makes the answer to the assigned shortcut question
replayable without private APIs.

**Failure mode.** The probe still shares the public input format and the declared
rival functions. Racket remains the final authority; the retained witness therefore
also has a supported `arcpuzzles apply` receipt.

## D7 — Evidence and prior work policy

No prior return was treated as current evidence. The immutable selected baseline was
measured directly, associated notes were empty, and every final count is tied to the
final generator hash. Failed baseline and intermediate battery summaries are kept;
oversized repetitive override rows are represented by a hash-bound compact failure
report with minimized witnesses.
