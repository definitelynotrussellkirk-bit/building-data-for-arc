# Working notes: 4c0d744296ec

## Intended rule and authority

The input is a zero-background grid whose only nonzero cells are distinct-color
markers in row 0. Each marker color is copied down its complete column; unmarked
columns remain zero. The authoritative Racket row was not changed. The generator
is pinned to canonical `RULE_HASH = c508f4ec9417`.

## Baseline finding → current decision

The selected v1.1.1 baseline declared nine controls although only height, width,
and marker count could affect pixels. Several palette/texture controls were dead,
unknown controls were silently accepted, declared ranges did not match generation,
colors could repeat despite an `n_distinct_colors` axis, and negative textures
returned inputs outside the stated manifold. The focused baseline override audit
reported 9,449 findings across 78,390 attempts, exact canonical-profile support
was 0/60, and the semantic gate reported `NO_CONTRACT`.

Version 2.0.0 replaces that contract with three constructive, observable axes:
`grid_h` 6..12, `grid_w` 8..14, and `markers` 2..6. Unknown, wrong-type, and
out-of-range overrides are rejected; `observe_overrides` recovers every declared
axis. Markers use distinct colors 1..9, and `self_check` now rejects malformed,
ragged, noisy-body, duplicate-color, vacuous, or illegal-color inputs.

## Distribution choices

A two-thirds canonical-profile branch anchors each difficulty band to the five
canonical `(height, width, nonzero-marker-count)` profiles. A broad branch still
covers every declared height, width, and marker-count value. Difficulty only
reweights lawful small/large incidental dimensions; exact overrides remain
honored in every band. Marker columns and marker colors are keyed independently.

Distinct colors are intentional: they preserve the canonical support and ensure
that a learner must retain each marker's color rather than merely identify marked
columns. Repeated-color cases remain outside this reviewed sampler's declared
manifold; the Racket rule itself is more permissive.

## Semantic contract and retained witness

The task declares two executable rivals: `top_row_only` (no projection) and
`single_color_projection` (project every marked column using the first color).
The `multiple_marker_colors` witness fires on every generated input and refutes
both rivals. A source-bound counterexample is retained at
`counterexamples/semantic-rivals.json` and covered by the task-local regression
suite.

## Final evidence

Final generator SHA-256:
`4fc11b52308efea4793909e9675d2a7f090282a3fa1d5d5eaee8c4fed2d24ae8`.

- Full after battery: 12/12 stages green, `checks/after/`.
- Portable task tests: 29/29 passed, `checks/task-tests/`.
- Profile floor: 28/60 exact and 36/60 envelope hits; every band supported.
- Semantic smoke: 600/600 strict draws, 60/60 rival checks, 12/12 lessons
  identifiable, and 0/48 ambiguous query rotations.
- Larger census: 300/300 lessons, 0/1,200 production ambiguities and 0/1,200
  rotation ambiguities across 1,191 unique inputs.
- Exposed post-repair solve: revision 1 passed all 3 visible demonstrations.

## Known limits and open findings

The declared-rival checks are finite and do not prove uniqueness against every
possible hypothesis. The generator intentionally excludes empty/full marker rows,
body noise, repeated marker colors, widths below 8, and heights below 6. Those are
lawful or adversarial extensions the Racket program may handle, but they are not
claimed by this training distribution. No remaining blocker was found for the
reviewed domain.
## Current reviewer considerations

Source SHA-256: `4fc11b52308efea4793909e9675d2a7f090282a3fa1d5d5eaee8c4fed2d24ae8`.

# Decisions for 4c0d744296ec

Final generator SHA-256: `4fc11b52308efea4793909e9675d2a7f090282a3fa1d5d5eaee8c4fed2d24ae8`.
The selected baseline was reviewed directly; no earlier return was used as a
measurement substitute. Historical notes for this task were empty.

## D1 — Replace the advertised axis surface instead of emulating dead controls

**Prior choice.** Version 1.1.1 advertised nine axes: height, width,
`palette_kind`, `markers`, `palette_size`, `position_bias`,
`n_distinct_colors`, `marker_density`, and `texture`. The source comments do not
preserve why those controls were chosen; the apparent intent was generic
combinatorial breadth plus negative textures.

**Problem.** Most controls never changed the returned grid. Declared endpoint
ranges also exceeded constructive support. Unknown controls were accepted, and
negative textures bypassed the ordinary sampler. The focused baseline override
run produced 9,449 findings over 78,390 attempts
(`checks/before-focused/override/`).

**Decision.** Advertise only `grid_h`, `grid_w`, and `markers`, because each is
constructive and directly recoverable from pixels. Add strict unknown/type/range
rejection and `observe_overrides`.

**Rejected alternative.** Keep the generic axes and invent cosmetic palette
meanings. That would enlarge the interface without adding rule-relevant
variation, and it would preserve opportunities for silent no-ops.

**Probe.** The portable suite exercises min/max exact controls in every band and
invalid controls. The final override gate accepted 12,690/12,690 lawful draws
across 141 cases and reported zero findings (`checks/after/`).

**Limit.** The smaller contract deliberately gives up generic compatibility with
callers that relied on undocumented dead controls. Such calls now fail loudly.

## D2 — Mix canonical anchors with broad lawful coverage

**Prior choice.** Height was sampled from 7..12 and width from 8..14, with narrow
band-specific ranges. The declared valid range was 2..24. Marker count defaulted
to 3..6. None of the 60 baseline profile-floor draws exactly matched a canonical
profile, and hard had zero envelope hits.

**Decision.** Use five exact canonical `(height, width, marker-count)` anchors in
a weighted two-thirds branch, plus a broad branch spanning height 6..12, width
8..14, and 2..6 markers. Difficulty supplies only soft lawful weighting. Exact
overrides take precedence in every band.

**Rejected alternatives.** Canonical-only sampling would overfit five small
profiles and reduce input diversity. Broad uniform-only sampling reproduced the
observed support-floor failure. A rejection sampler was unnecessary because all
joint combinations are constructive.

**Probe.** The final profile floor has 28/60 exact and 36/60 envelope hits, with
exact support in easy, medium, and hard. In 80 draws per band the task-local tests
require at least 12 distinct profiles, at least 76 distinct inputs, and regular
edge-marker coverage.

**Limit.** The declared shape envelope is narrower than the Racket program's
mathematical domain. This is a training-distribution decision, not an authority
restriction.

## D3 — Require distinct marker colors

**Prior choice.** Each marker independently sampled a color, so colors could
repeat even while `n_distinct_colors` was advertised. This weakened the evidence
that each top-row color, not just each marked column, controls its output stripe.

**Decision.** Sample marker colors without replacement from 1..9 and require
2..6 markers. This makes every ordinary input a witness against a plausible
single-color projection rival.

**Rejected alternatives.** Allow arbitrary repeats and rely on occasional
multi-color examples. That creates lessons in which the single-color rival can
fit by accident. Adding a separate color-count axis would reintroduce a coupled
contract without a demonstrated need.

**Probe.** The semantic gate observed `multiple_marker_colors` on 600/600 draws;
60/60 checked witness instances refuted both named rivals. The retained exact
witness is `repo/generators/4c0d744296ec/counterexamples/semantic-rivals.json`.

**Limit.** Repeated-color top rows are lawful under the authority but not sampled.

## D4 — Make validation fail closed

**Prior choice.** `self_check` verified only that the grid was nonempty, the body
was blank, and at least one marker existed. It did not enforce rectangularity,
ARC colors, declared dimensions, marker bounds, or distinctness.

**Decision.** Validate container shape, row widths, integer colors 0..9, shape
bounds, blank body, 2..6 markers, and unique marker colors. Malformed inputs
return diagnostics rather than raising.

**Rejected alternative.** Depend on `generate` being correct and keep a permissive
validator. That would leave canonical support, mutation tests, and future tooling
unable to distinguish the intended training manifold from accidental inputs.

**Probe.** Mutation tests cover empty/ragged grids, body noise, no markers,
duplicate colors, illegal values, and non-integer booleans. All 29 final tests
pass.

## D5 — Add executable semantic competitors and a source-bound lesson census

**Prior choice.** No strict hook, witnesses, competitors, or lesson check existed;
the baseline semantic status was `NO_CONTRACT`.

**Decision.** Declare `top_row_only` and `single_color_projection` in both
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`; bind them to the
`multiple_marker_colors` witness; use three demonstrations per lesson. Retain a
small exact counterexample and run both the standard semantic smoke and the larger
query-rotation census.

**Rejected alternatives.** A prose-only claim cannot be source-bound or replayed.
A one-demo curriculum would show the transformation here but provides less
protection against accidental lesson construction and future distribution edits.

**Probe.** The smoke materialized 12/12 identifiable three-demo lessons with
0/48 ambiguous rotations. The larger production census materialized 300/300
lessons, 1,200 pairs, and 1,200 query rotations with zero declared-rival
ambiguities and 1,191 unique inputs (`checks/lesson-census.json`).

**Limit.** These two rivals are not an exhaustive hypothesis class. The result is
finite evidence, not a proof of universal identifiability.

## D6 — Preserve the Racket authority

The canonical program already matches all five canonical pairs and the intended
projection rule. No output-law defect was reproduced, so changing the authority
would add risk without solving the generator defects. `RULE_HASH` is pinned to
`c508f4ec9417`; rule smoke, Racket lint, and authority synchronization are green.

## D7 — Keep failures and source-bound tooling

The initial aggregate before battery remained interrupted/running after partial
stage evidence and is not reported as a pass. Focused before runs retain the
reproducible defects. The first parallel after defect-lint attempt exited 247
under contention; the sequential retry and completed full battery are retained
separately. Red task-test evidence records 13 failures before implementation;
the same 29 tests later pass.

The task-local test module uses `reviewer_support.find_root` and
`canonical_pairs`, so it remains portable after packaging. The semantic
counterexample JSON records source hash, seed, sample index, overrides, intended
output, rival outputs, and differing cells for future agents.
