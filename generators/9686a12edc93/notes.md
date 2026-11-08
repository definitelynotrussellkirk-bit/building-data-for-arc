# Working notes: 9686a12edc93

## Current rule and sampler

The selected canonical Racket rule (`RULE_HASH = 74f975abb98b`) is unchanged. It starts from an empty grid and, for each nonzero color occurring exactly twice, draws the inclusive horizontal or vertical segment only when every interior input cell is zero. Non-pairs, unaligned pairs, and blocked pairs contribute nothing.

Version `3.0.0` exposes only three exact controls: `grid_h` 7..16, `grid_w` 9..18, and the number `n` of clear pairs 1..5. A constructive D4-transformed template realizes every joint extreme without retries, and `observe_overrides` plus `self_check` verify the requested values. Explicit override calls always include one blocked-pair counterexample so a single requested instance is discriminating.

## Teaching schedule and decision reversal

The canonical demonstrations contain only clear pairs. Therefore the strongest simple canonical-fitting rival is `ignore_clearance`: connect every exactly-twice axis-aligned pair even when a nonzero interior cell blocks the span.

The first v3 draft put a blocked pair in every generated input. That refuted the rival but defect lint correctly found a `palette_roles` mismatch: canonical inputs preserve every input color, while every generated output removed the blocker color. The final five-step schedule reverses that choice:

- residues 0 and 2 are clear-only canonical-role anchors;
- residues 1, 3, and 4 contain one blocked pair crossing an endpoint of a clear pair;
- every three consecutive examples contains at least one blocker witness;
- the first three residues hit the canonical size/palette profiles `(8,9,4)`, `(9,10,4)`, and `(10,10,5)` in every difficulty band.

The retained exact witness is under `counterexamples/ignore_clearance/`; the independent analyzer/oracle for future reviewers is `workspace/reference_probe.py`.

## Validation and limits

Task-local tests cover strict scalar rejection, all control extremes, deterministic replay, D4 layout variation, canonical Racket parity, canonical fit of the rival, exact blocker disagreement, and every cyclic three-demonstration start. Source-bound schedule and production lesson censuses are retained in the review return.

Finite checks cover the declared `ignore_clearance` rival and generic census rivals; they are not a proof of universal identifiability. Fixed-seed period enumeration covers all five starts in all three bands at seed 0, not all seeds. The sampler intentionally uses a small constructive motif family under D4 transforms and translations; this is sufficient for the reviewed controls but does not exhaust all legal clear/blocked pair geometries.
## Current reviewer considerations

Source SHA-256: `f9310b3189afc01f5fff782bbf95e50f53408b9374763132400a3deb148668b6`.

# Decisions for 9686a12edc93

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical Racket program unchanged and pin `RULE_HASH = "74f975abb98b"`.

**Reason.** Canonical examples, the selected runtime, and an independent Python mirror agree on the law: start from an empty output; draw an exactly-twice same-color horizontal/vertical pair only when every interior input cell is zero. The defect was in sampling and teaching, not the authority.

**Alternatives rejected.** Changing the rule to connect through blockers, copying the input before drawing, or adding behavior for unaligned/non-pair colors would alter the task rather than repair its generator.

**Evidence.** `checks/after/checks/9686a12edc93_after_rule_smoke.json`, `checks/after/checks/9686a12edc93_after_authority_sync.log`, and `generators/9686a12edc93/counterexamples/ignore_clearance/racket.json`.

## D2 — Replace decorative controls with three exact axes

**Choice.** Expose only `grid_h` (7..16), `grid_w` (9..18), and `n` (1..5 clear pairs). Validate seed, sample index, difficulty, unknown keys, types, and bounds before generation. Make `observe_overrides` return exactly those realized values.

**Original rationale.** Unknown. Version 2 advertised palette, density, position, distinct-color, and texture controls that did not change the draw; negative textures were mixed into the normal valid domain.

**Alternatives rejected.** Keeping compatibility aliases would preserve silently ignored controls and continue to misstate the input distribution. Adding many new controls was unnecessary for this repair and would enlarge the unverified joint space.

**Failure modes checked.** Boolean-as-integer, float/string integers, negative sample indices, unknown keys, every axis extreme, partial overrides, and all difficulty bands. The focused suite checks direct observability; the final battery checks override matrices.

**Evidence.** Baseline findings in `checks/before/checks/9686a12edc93_before_lint.log` and `checks/before/checks/9686a12edc93_before_defect_lint.log`; final results in `checks/task-tests/` and `checks/after/checks/9686a12edc93_after_override.json`.

## D3 — Use a constructive D4 template instead of retry placement

**Choice.** Place prefixes of five pairwise-disjoint clear paths in a 6×7 base template, then apply rotation/reflection and translate it inside the requested canvas. An optional blocked path crosses one clear endpoint as its sole nonzero interior cell.

**Reason.** This realizes every legal joint extreme deterministically, including 7×9 with five clear pairs, without rejection loops or hidden infeasible combinations. D4 transforms and translations vary orientation and position while preserving the exact semantic relation.

**Alternatives rejected.** The old random retry placer generated only clear paths and made exact extreme support harder to prove. A larger procedural geometry family would add complexity without improving the specific teaching defect.

**Known limit.** The legal task domain is broader than one motif family under D4 and translation. The reviewed sampler does not claim exhaustive geometry support.

## D4 — Declare and retain the strongest canonical-fitting rival

**Choice.** Declare `ignore_clearance`: connect every exactly-twice axis-aligned pair even when an interior input cell is nonzero. Retain one exact generated counterexample and expose an independent analyzer/oracle in `workspace/reference_probe.py`.

**Reason.** All three canonical demonstrations have clear interiors, so this rival fits every canonical pair. It differs from the intended rule exactly on blocked aligned pairs and is simpler than many copy/noise alternatives.

**Witness.** Seed 91, sample index 4, overrides `grid_h=7, grid_w=9, n=1`. The selected Racket output draws only color 2 horizontally; the rival additionally draws color 5 vertically through the color-2 endpoint. Exact evidence is in `generators/9686a12edc93/counterexamples/ignore_clearance/witness.json`.

**Limit.** Passing a finite declared-rival census does not establish universal identifiability against every possible hypothesis.

## D5 — Reverse “blocker in every draw” into a five-step mixed schedule

**First choice.** The first v3 draft emitted a blocked pair in every generated input. This guaranteed a single-example rival witness.

**Observed failure.** Strict defect lint reported `generator/authority structural mismatch: palette_roles`: every canonical input color survives, while the always-blocked draft removed one input color in every output. See `checks/after-v1/checks/9686a12edc93_after_defect_lint.log`.

**Final choice.** Use schedule residues 0 and 2 as clear-only canonical-role anchors and residues 1, 3, and 4 as blocker lessons. Every three consecutive examples includes at least one blocker. Residues 0..2 also realize the canonical size/palette profiles `(8,9,4)`, `(9,10,4)`, and `(10,10,5)`.

**Why this balance.** It preserves canonical structural support while making the zero-interior condition unavoidable in every normal three-demonstration lesson. Independent structural comparison then reported no mismatch, and the final defect lint passed.

**Alternatives rejected.** Clear-only generation leaves `ignore_clearance` unrefuted. Always-blocked generation erases canonical palette-role support. Random blocker insertion can create unlucky all-clear demonstration windows unless the materializer rejects/resamples them.

## D6 — Make direct override calls self-contained counterexamples

**Choice.** Any non-`None` explicit override causes that single generated grid to include the blocked pair, regardless of schedule residue.

**Reason.** The override API is commonly probed one instance at a time. Requiring a surrounding schedule to understand a directly requested `n`, height, or width would make exact-control tests semantically weak.

**Trade-off.** A default clear-only residue and the same numeric controls can differ in blocker presence when an explicit override is supplied. This is intentional and documented; the advertised axes describe exact dimensions and clear-pair count, not blocker presence.

## D7 — Use three demonstrations and require rotation evidence

**Choice.** Keep `EXAMPLES_NEEDED = 3`, declare `LESSON_SCHEDULE_PERIOD = 5`, and require query-rotation checks rather than treating them as advisory.

**Production policy.** Lessons contain three demonstrations and one query in materializer order. The five-step schedule guarantees a blocker in every consecutive three-example demonstration window.

**Measured evidence.** Fixed-seed exhaustive enumeration covered all 5 start residues × 3 bands = 15 lessons and all 60 query positions, with zero ambiguities/errors. The production census covered 100 lessons per band = 300 lessons and all 1,200 query rotations, also with zero ambiguities/errors. See `checks/schedule-period-s0.summary.json` and `checks/lesson-census-100.summary.json`.

**Limit.** Fixed-seed enumeration proves only seed 0 across the declared residues/bands; random census is finite and does not enumerate all seeds or undeclared rivals.

## D8 — Keep the authoritative output empty-first

**Choice.** Both the generator mirror and independent probe start from an all-zero output, then add only valid clear segments.

**Reason.** Starting from a copy of the input accidentally preserves blocked endpoints and other invalid motifs. That shortcut happens to fit clear-only canonical examples but is not the selected law.

**Probe.** `workspace/reference_probe.py` includes both `intended_output` and `copy_then_connect`, plus exact differing-cell reporting, so future agents can test this boundary without importing generator internals.


## Native parametric design

Build `clearance_stage = input | painted` as a separate native family. Preserve
exact canonical bytes for `input`. For `painted`, process original endpoint pairs
in ascending numeric color order, checking each interior against original input
plus only accepted earlier segments. Output starts empty. Accepted paths update
occupancy and output; rejected paths update neither. An accepted-rejected-accepted
crossing chain demonstrates the state dependency and distinguishes occupancy of
actual accepted paths from occupancy of every earlier candidate.

The protected Racket `grid-colors` sorts numeric colors. The existing independent
probe's reading-order assumption was unobservable in production's disjoint clear
paths but matters in the broader native crossing grammar. Reuse production's pure
segment helper and implement the protected numeric order in the native mirror;
leave production and the historical probe unchanged. Numeric priority is shared
by both settings so the parameter isolates the clearance surface.

The native grammar admits exact-list integer 0..9 rectangular grids with axes 3..30,
including empty/all-invalid cases and arbitrary color multiplicities. Pair
locations always come from the original input. Singletons, triples, unaligned
pairs and blocked endpoints remain occupancy blockers, yet disappear from the
empty-first output. Adjacent endpoints remain valid. Use three mandatory demos,
up to six total, and four independently generated novel query roles; construct
and shuffle the complete query bank before slicing a requested prefix. Keep
palette/geometry priorities counterbalanced in the demonstrations.

The public-evaluation focus `142ca369` supplies inspiration for line interactions
and visible context controlling continuation, not verified lineage or semantic
equivalence. Preserve the broader difficulty through accepted-path state and
crossing/blocked/nonpair cases. Thirty-by-thirty pair-only inputs have at most 18
occupied source cells; measure their substantial line-output span separately.
Focused tests, bounded protected shortcut review, native qualification, causal
replay and public permutation checks determine reviewer readiness. The owner
must separately qualify and freshly accept both exact integrated sources.


## Native teaching repair: retain older accepted paths

The first bounded core audit passed 70 comparisons, but independent protected
review found a stronger wrong rule: retain original input plus only the latest
accepted path. It fit all three demos at painted seeds 0 and 17 and then disagreed
with queries, including 30x30 cases with 53 and 52 changed cells. The baseline
sources and failing reports are retained, not reused as current passing evidence.

Strengthen the existing chain with a fourth, higher-color candidate crossing the
first accepted path while avoiding the third. Intended acceptance is true, false,
true, false; last-only memory falsely accepts the fourth. Preserve the other
teaching roles and keep the minimum at three demonstrations. Promote this observed
rival into the task-local audit menu with a strict private memory control. A compact
4x5 protected reproduction changes three cells; its program, labels and trace are
retained in checks/9686a12edc93/memory-regression.json. Rerun the same independent
menu on a new frozen snapshot before qualification; do not expand the hypothesis
menu after the repair or overwrite the historical evidence.

## Native reviewer readiness

The repaired source passes 120 focused tests and 72 protected core comparisons,
all demo-refuted. Replaying the same independent three-rival menu gives 6
demo-refuted and 6 input-mode behaviorally inert finite-consistent comparisons,
with no query conflicts. The original two memory conflicts remain historical.
Twenty maximum-count/max-seed labels match protected Racket. Native qualification
passes four setting/seed jobs with 40 Racket evaluations. Both source-bound causal
cases replay successfully; 16 saved public views pass pairing, early-stop and
private-field checks, with four corruption cases rejected. Intended setting
program texts stayed byte-identical through the sampler repair. Three demos
remain sufficient for the tested menu. These finite results complete reviewer
construction, not owner acceptance or training admission. The next action is
fresh owner qualification and acceptance of both exact integrated sources.
