# Working notes: 9bde2c3e0346

## Intended rule and authority

For every four-connected nonzero object, draw only the border of its bounding
box in that object's color on a blank output. The selected canonical Racket rule
is unchanged and pinned as `8f9e53b42241`; Python `rule_mirror` is diagnostic,
not label authority.

## Baseline defect and prior lead

Baseline generator SHA
`b2eaa8f64feff024e05a33769d19c71022720945eb9178f474754fee84dd2979`
documented a **solid filled rectangle** and exposed nine overlapping or inert
controls. Its validator also admitted no-op/degenerate scenes and did not pin the
rule. Prior return `review-7132503a14071f18:v0001` was used only as a lead; this
review independently reproduced its seed-0 semantic mismatch against actual
Racket execution before repair.

## Current decisions

- Replaced the baseline sampler with version `3.0.0`; the Racket authority was
  not edited.
- Reduced the contract to three exact, pixel-observable integer controls:
  `grid_h`, `grid_w`, and `n_objects`. Unknown, retired, bool, string, float, and
  out-of-range overrides fail explicitly.
- Weighted canonical profiles `(8,8,2)` and `(9,9,2)` in every band while keeping
  all legal sizes/counts reachable.
- Every generated scene includes a connected 3×3 object with both a colored
  interior cell and missing frame cells. Companion objects and placements vary.
  This simultaneously teaches adding the border and clearing interiors.
- Declared four executable rivals and a source-bound lesson hook. The specific
  canonical-fitting shortcut `add_frame_keep_interior` fits all 3 canonical
  pairs but differs on the retained Racket-verified case at
  `counterexamples/interior-retention-shortcut/case.json`.
- Rejected the smaller alternative of correcting prose only. That would leave
  canonical-like L shapes compatible with retaining interior pixels and would
  not repair the override contract.

## Verification and limits

The repaired generator passed all 12 battery stages, 37 portable focused tests,
150 joint exact-axis cases, 33 independent Racket comparisons, and 300 local
schedule rotations. The production census materialized 300 lessons / 600 pairs
and checked 600 held-out rotations with zero declared-rival ambiguity or hook
warnings. These are finite checks against declared rivals, not a proof of unique
induction against every conceivable rule.

The strict sampler intentionally covers 2–3 distinct-color objects of 3–5 cells
with 2×2 through 3×3 disjoint bounding boxes. Other lawful uses of the canonical
Racket program are outside this generator's declared training manifold.
## Current reviewer considerations

Source SHA-256: `d1e650cd3e6c97262d5100d99024bee51bc2df7f24abe553a4f309b68c98d04e`.

# Decisions for 9bde2c3e0346

## D1 — Keep the selected Racket authority unchanged

**Choice.** Preserve the canonical program and pin `RULE_HASH = "8f9e53b42241"`.
The intended transformation is: for each four-connected nonzero component, draw
only the border of its axis-aligned bounding box in that component's color on a
blank output.

**Rationale and evidence.** Actual Racket execution matched an independent
component/frame implementation on all three canonical inputs and 30 generated
inputs (`checks/bbox-frame-probe.json`, 33 parity cases total). The baseline's
solid-rectangle prose and sampler disagreed with the authority; changing the
authority to fit that sampler would reverse the selected task rather than repair
the data generator.

**Alternative rejected.** Reinterpret the canonical task as filled rectangles.
Rejected because the published outputs and selected Racket program erase object
interiors and render only frames.

## D2 — Replace the baseline distribution rather than patch its prose

**Prior choice.** The baseline generator (SHA-256
`b2eaa8f64feff024e05a33769d19c71022720945eb9178f474754fee84dd2979`)
sampled solid or texture-like bounding-box fills, exposed overlapping/inert
controls, and did not pin the rule. Its original rationale is not recorded; the
current code and prose consistently reflected the wrong solid-fill behavior.

**New choice.** Version `3.0.0` constructs two or three separated, distinct-color,
four-connected objects on 8×8 through 12×12 grids. Object bounding boxes are
2×2 through 3×3 and disjoint. The output remains Racket-authored.

**Why.** Constructive sampling makes the intended component and frame roles
observable, avoids no-op scenes, and provides a bounded domain that the validator
can check exactly. The repaired battery is 12/12 green, compared with the
baseline's 7 green, 2 advisory, and 3 failed stages.

**Limit.** The canonical program may handle larger grids, overlapping boxes,
more objects, repeated colors, or larger components; those cases remain outside
this generator's declared training manifold.

## D3 — Require simultaneous “add border” and “erase interior” witnesses

**Choice.** Every ordinary sample includes one connected 3×3 object containing
an original interior cell while omitting at least one bounding-box border cell.
Companion objects and placements vary.

**Why.** The three canonical examples all permit the shortcut “add the missing
frame but retain every original cell.” That rival fits 3/3 canonical pairs. A
single generated demonstration must therefore show both positive construction
and destructive clearing. The retained Racket-labelled counterexample is
`repo/generators/9bde2c3e0346/counterexamples/interior-retention-shortcut/case.json`;
at `(2,2)` the authority returns 0 while the shortcut returns color 4.

**Alternatives rejected.** (1) Correct only the summary text: labels would remain
shortcut-compatible. (2) Rely on witness frequency across unrelated lessons:
individual learners receive one demonstration, so each complete lesson must
carry the distinction itself. (3) Use only filled objects: that teaches erasure
but not addition; use only hollow/incomplete frames: that teaches addition but
not erasure.

## D4 — Expose only exact, pixel-observable controls

**Choice.** Retain `grid_h` and `grid_w` in 8..12 and `n_objects` in 2..3. Reject
unknown, retired, noninteger (including bool), and out-of-range controls.

**Why.** These values are recoverable from the emitted grid and can be tested
jointly. `checks/bbox-frame-probe.json` exhausts all 150 combinations of five
heights × five widths × two object counts × three bands. The baseline's nine
controls included aliases, inert tokens, silently ignored unknown keys, and
values whose advertised domains did not match generation.

**Failure mode considered.** Small grids might make three placements impossible.
The chosen shape library and backtracking placement were exercised for every
joint combination without rejection. The generator raises rather than silently
substituting a different requested value.

## D5 — Weight canonical profiles without collapsing support

**Choice.** Weight `(8,8,2)` and `(9,9,2)` profiles in every difficulty band while
keeping all 8..12 sizes and both object counts reachable. Difficulty only changes
weights, not semantics.

**Why.** The profile-floor gate needs canonical-scale support in every band, but
a generator that emits only two layouts would have poor variety. In 100 defaults
per band, the reusable probe found 56, 45, and 48 canonical-profile hits in easy,
medium, and hard respectively, with 100 unique inputs in each band.

**Limit.** These are seeded finite samples, not a proof of the exact long-run
probability of every profile.

## D6 — One demonstration per lesson; arbitrary held-out pair rotation required

**Choice.** `EXAMPLES_NEEDED = 1`. Production assembly uses one demonstration and
one query. The lesson hook requires every declared rival to be refuted by the
demonstration. Query rotation policy is `require`, not diagnostic-only.

**Evidence.** The production census materialized 300/300 lessons (100 per band),
600 unique input/output pairs, and 600 held-out rotations. Production and
rotation verdicts were both `no_ambiguity_found`, with zero materialization,
hook, scoring, or declared-rival errors. The independent probe additionally
checked 300 short-lesson rotations. These are finite checks against the nine
reported declaration entries (four unique rival behaviors plus aliases), not a
proof of unique induction against all conceivable rules.

## D7 — Tests and reusable probe are independent of the generator mirror

**Choice.** The focused test oracle reconstructs components and frames separately,
then binds it to canonical labels and actual Racket execution. The reusable
`workspace/probe_bbox_frames.py` exhausts joint controls, samples default
profiles, checks declared rivals and lesson rotations, and calls the supported
Racket authority.

**Why.** Comparing the generator's mirror only with itself would reproduce an
implementation bug rather than detect it. The regression was written and
observed failing first: 28 failed / 9 passed on baseline, then 37/37 passed after
repair.

## D8 — Prior evidence used only as a lead

The retained return `review-7132503a14071f18:v0001` identified a possible
semantic mismatch. I did not adopt its claims as measurements. The baseline
mismatch was independently reproduced against the current source and actual
Racket output before any repair; the new failure and final receipts are retained
under `checks/`.
