# Working notes: 954070a7d7ce

Review assignment `review-39ca466c1586c929`; no reroll. Imported associated notes
remain unchanged in `evidence/associated_notes.jsonl`.

## Measured defects in 1.1.1

The checker counted pixels instead of validating objects. Declared overrides
were inert, unknown keys were ignored, and metadata could admit invalid texture
scenes. Random placement silently omitted the requested second frame in 133/258
attempts in a fixed 600-draw census. Frame sizes were fixed to 6/7. Distinct colors
per frame meant a color-global rival fit all five canonical pairs and all 600
generated examples tested.

## Landed repair

Version 2.0.2 introduces exact constructive placement, strict object/marker
validation, four real observable override axes, 4..9 frame sides, and scheduled
same-color multi-frame counterexamples. `RULE_HASH=285c825480d1` pins the existing
canonical program. No Racket or shared source was changed.

The initial uniform canvas distribution failed the canonical profile floor.
A failed follow-up mutated the pre-context copy of overrides. Both source
snapshots and failures remain in the returned review; the final context-map fix
passes the original gate without weakening it. Exact-profile support is 3/60,
so this is a pass at the threshold, not a claim of abundant margin.

## Verification and reuse

Authoring tools and tests are task-local. The final review's `checks/after-v3/`
and `checks/probe-v202/` correspond to version 2.0.2; earlier directories retain
actual failed/intermediate runs. Do not choose a report by the word "final" in
its filename: compare the full generator hash. `workspace/README.md` gives
reproduction commands and the next-agent handoff.

## Limits

One or two nonnested separated rectangular frames only. Fixed background/wall
semantics are intentional; removed nominal texture/palette keys are not supported.
Scheduled witness coverage assumes four consecutive indices with a fixed seed
and no conflicting overrides. No trained-model score, masked solve score, global
rule uniqueness, or training-safety approval is claimed. Audits of other tasks
are findings-only and their files were not modified.
## Current reviewer considerations

Source SHA-256: `a2288e64d15c0773254b2a42696a8ef58dd1b24148c4b0ab6f2c23ca94c0c25d`.

# Distribution decisions — 954070a7d7ce

Review `review-39ca466c1586c929`; generator 1.1.1 → **2.0.2**. No Racket source,
canonical pair, catalog approval, shared helper, or other generator was changed.
The imported rationale is unknown except where encoded in its source. The
following choices are reviewer decisions, not claims about original author intent.

## 1. Keep the semantic task; make placement exact

Retain background 0, wall color 9, marker colors 1..8, and one or two hollow
rectangular frames. Retain the paired top/left marker convention and exclude
their shared corner. The canonical five pairs and unchanged Racket authority
support these choices. The original already aimed at 1–2 frames, but a bounded
random-placement loop silently discarded the second frame in **133 of 258**
requests in the 600-draw baseline census (`checks/probe-before/report.json`).

Partition the canvas into one or two slots before sampling each frame. Two slots
have a full zero-cell gap and can be horizontal or vertical. Each contains one
frame; postconditions check geometry, frame count, and realized marker-color
count. Reject an impossible request rather than silently repair its meaning.
An unconstrained retry loop, returning fewer objects, and increasing the object
count to three or more were rejected: the first two violate count semantics, and
the third expands this task unnecessarily. Slotted layouts restrict arbitrary
interleavings; they are not a uniform sampler over all legal frame placements.

## 2. Frame sizes and canvases

Frame sides vary from 4 through 9 subject to the available slot, rather than the
original 6/7-only geometry. Width 4 occurs in canonical examples. Rectangles,
small interiors, different offsets, and edge placement reduce fixed-size and
fixed-position cues. Larger sides remain bounded to avoid filling the canvas
with a single unrelated visual regime. Racket parity is checked on generated
cases rather than inferred from the shape constraints.

Supported canvas overrides are height 9..14 and width 11..20 at every difficulty.
These lower bounds permit two 4×4 frames with a separating cell in either
orientation. Original difficulty-dependent bounds disagreed with declared
bounds. Different difficulty tags seed different layouts but do not change the
valid override domain; no measured easy/medium/hard learning difficulty is claimed.

A first implementation sampled these canvas ranges uniformly and failed the
canonical profile gate: exact-profile 1/60, with six downstream stages pending.
The replacement uses an **80% canonical-scale / 20% full-range mixture**. The
canonical-scale branch samples height 9..12 and width 11..15, not complete
canonical grids. Full-range sampling can itself land in that rectangle, so the
realized in-envelope fraction is not claimed to be exactly 80%. Explicit supplied
sizes always win, including one-dimension overrides.

The final gate has exact-profile **3/60** and envelope **52/60**; the exact-profile
result is at the gate's minimum, not a large margin. A separate 240-seed regression
requires substantial envelope mass while retaining larger examples. The second
implementation initially updated a dictionary that `gen_ctx` had copied; its
failed regression and battery are preserved. Version 2.0.2 updates the context's
actual override map. Evidence: `checks/tests-scale-red.log`,
`checks/tests-green-v201.log`, `checks/tests-green-v202.log`, `checks/after/`,
`checks/after-v2/`, and **`checks/after-v3/`**. No gate threshold was relaxed.

## 3. Color is not frame identity

The strongest tested canonical-fitting rival completes only the first frame of
each color. Every canonical pair has distinct frame colors, so all five pairs
fit that shortcut. The original generator never reused a color across frames:
0/600 generated cases challenged it. The replacement exposes exact
`n_distinct_colors` and deliberately includes two frames sharing one color.

A seed-rotated four-index schedule covers single frame, distinct-color frames,
shared-color horizontal frames, and shared-color vertical frames. Every four
consecutive unoverridden indices for a fixed seed include both shared-color
profiles. It is a lesson-coverage device, not a guarantee for arbitrarily
subsampled indices, independent seeds, fewer demonstrations, or explicit
overrides that remove shared colors. No output encodes the profile or index.

Pure independent random sampling was rejected because a short lesson could miss
the essential counterexample. Always using repeated colors was rejected because
it would remove canonical-like distinct-color examples. The final independent
600-draw probe found **297** shared-color inputs, each with a Racket-confirmed
shortcut disagreement (`checks/probe-v202/`). The battery semantic cohort is a
*different* 600 inputs and found 298; these counts must not be mixed.

## 4. Replace inert or unsafe controls with observable controls

Expose only `grid_h`, `grid_w`, `n_frames`, and `n_distinct_colors`; accept `None`
as unspecified. Reject unknown names, out-of-domain integers, booleans, floats,
and numeric strings rather than silently ignoring or coercing them. Realized
axes are derived from the actual grid by `observe_overrides`, not echoed from
requested arguments. `n_frames=1, n_distinct_colors=2` is explicitly incompatible.
A color-count-only request of two forces enough frames; a frame-count-only
request of one forces one marker color.

This is an intentional major-version interface change. Prior nominal palette
and texture controls were inert or admitted invalid/no-op scenes. Maintaining
aliases would perpetuate misleading contracts. Destructive scenes now live in
`mutation_fixtures`, not ordinary generation. Consumers using removed override
keys must migrate; no backward-compatibility shim is promised.

The full 6×10 canvas matrix × 3 valid (frame count, color count) combinations ×
3 difficulty tags × 2 seeds = **1,080** cases checks actual counts and canonical
Racket outputs. This exhausts the stated axis combinations, not all possible
random layouts. Malformed/unknown overrides have dedicated rejection tests.

## 5. Validate objects, not pixel totals

The original checker could accept broken borders, solid blocks, mismatched
markers, or extra marks because it primarily counted colors. The new checker
finds 4-connected wall components, requires complete hollow rectangular borders,
checks separation, accounts for every marker, and requires exactly one matching
marker at each allowed axis location. Metadata cannot bypass these checks.

Nested, touching, nonrectangular, wrong-color, and extra-marker scenes are outside
this generator's domain even if the general Racket program returns some output.
Self-check validity is not claimed to equal the entire operational domain of
Racket. Final battery mutation sensitivity is 69/69 versus baseline 31/60; the
mutation pools differ, so these are separate rejection counts, not a paired
accuracy estimate. Dedicated task tests include direct semantic negatives.

## 6. Preserve label authority and state the evidence boundary

`RULE_HASH` pins the canonical program. `rule_mirror` is only a diagnostic hook;
training labels still come from Racket. The authoring probe independently
inventories components and compares its expected cross with actual Racket output.
The battery checks the named witnesses against their rivals and evaluates 12
lessons against the declared competitor set. This does not prove uniqueness
against every conceivable rule or improve a measured trained agent score.

Authority-sync reports the selected program synchronized and execution parity
passing. An existing divergent archival `raw_code` field remains unchanged, as
it did before the repair. Do not describe all archival source strings as equal.
The catalog remains **unapproved / training safety unverified**; maintainer replay
and admission are separate from reviewer tests.

## 7. Reusable work and honest solve provenance

Task-local tools retain exact seeds, source hashes, actual temporary runtime
paths, counts, and counterexamples. `review_probe.py` is for authoring;
`audit_probe.py` reproduces the two findings-only audits; `run_repository_tests.py`
runs the repository and task suites without editing shared code. Its disposable
interpreter uses explicit source and caller-dependency `.pth` entries because
runtime children intentionally discard `PYTHONPATH` and disable user sites.
The first nested-venv attempt could not find pytest; that failed attempt remains
in `checks/repository-final/` rather than being erased.

The fresh Python solve uses visible examples only during its solve phase, but
prior exposure from this repair is explicitly **yes**. One revision passes four
visible examples and 42 visible/metamorphic/execution probes; masked correctness
is withheld. `solve/SOLVE_NOTES.md` is an engineering work log, not a token trace.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-27fc065873ae1c00:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a2288e64d15c0773254b2a42696a8ef58dd1b24148c4b0ab6f2c23ca94c0c25d`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/954070a7d7ce/generator.py,unchanged SHA256 a2288e64d15c0773254b2a42696a8ef58dd1b24148c4b0ab6f2c23ca94c0c25d. No issue found within bounded source audit:48 portable tests,720 joint overrides atone seed/index,29 real Racket comparisons including5 canonical pairs,and5 destructive mutations rejected. No random teaching census,universal proof or new approval;target unchanged. No owner audit rerun or new target approval. Target-local receipts: `checks/audit/954070a7d7ce/.task-tests.check.lock` `checks/audit/954070a7d7ce/probe.json` `checks/audit/954070a7d7ce/probe.log` `checks/audit/954070a7d7ce/probe.py` `checks/audit/954070a7d7ce/racket.json` `checks/audit/954070a7d7ce/task-tests/checks/task_tests.xml` `checks/audit/954070a7d7ce/task-tests/progress.log` `checks/audit/954070a7d7ce/task-tests/result.json`

### Assessment or prior finding

## 954070a7d7ce

**No issue found in the bounded audit.** Selected source SHA-256
`a2288e64d15c0773254b2a42696a8ef58dd1b24148c4b0ab6f2c23ca94c0c25d`;
executed rule hash `285c825480d1`. The current review index has no unresolved
audit rows. Sources, tests, notes, catalog and approvals were left unchanged.

The isolated task-test stage passed **48/48 cases**, with no failures or skips
(`checks/audit/954070a7d7ce/task-tests/result.json`). A separate read-only probe
checked all **720** valid geometry/frame/color combinations across difficulty
None/easy/medium/hard: heights 9..14, widths 11..20, and (frames, marker-colors)
(1,1), (2,1), (2,2), at seed 71/index 11. Independent component/marker inspection
confirmed requested dimensions, frame count, marker-color count, deterministic
replay, unchanged inputs, and an output-changing local cross in every case.

Racket reference execution matched the independent expected cross for **29**
inputs: 24 minimum/maximum geometry cases across easy/hard and all three valid
frame/color pairs, plus all five canonical pairs. All five destructive mutation
fixtures were rejected. Evidence: `checks/audit/954070a7d7ce/probe.json`,
`checks/audit/954070a7d7ce/racket.json`,
`checks/audit/954070a7d7ce/probe.py`, and
`checks/audit/954070a7d7ce/probe.log`. The probe exited 0.

This is finite coverage of one seed/index for the override matrix and selected
reference examples. It is not an exhaustive random-layout or teaching census,
proof against undeclared rivals, safety approval, or a claim about model scores.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
