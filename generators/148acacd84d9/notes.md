# Working notes: 148acacd84d9 — version 2.0.1

## Intended rule and domain

Rotate the complete input canvas 90 degrees clockwise, preserving zero margins
and every color. The canonical Racket rule is unchanged and pinned by
`RULE_HASH = 2f0ece3d3c8f`; Racket remains the label authority. Default inputs are
sparse multicolor squares, side 4..12, with 3..12 foreground cells, integer
colors 0..9, zero background, and 3..10 total colors including zero.

The four exact controls are `grid_h`, `grid_w` (4..12), `mark_count` (3..12),
and `palette_size` (3..10 **including zero**). Independent dimension overrides
also permit rectangles; default square lessons do not establish rectangular
generalization. `palette_size > mark_count + 1` is explicitly incompatible.
Non-integers, booleans, unknown keys, and removed controls raise `ValueError`.
The three `texture` diagnostics are reference-lawful but intentionally outside
the normal teaching validator; they are never sampled into default lessons.

## Decisions and reversals

- Replaced v1.3.0's ignored size/palette/corner/asymmetry/helper controls with
  four observable exact controls. Original broad metadata was not reliable.
- Replaced default rectangles with alternating canonical-size (4..6) and
  larger (7..12) squares in every band. Difficulty changes weights, not accepted
  override ranges. The 5×5 canonical slot permits total palettes four and five.
- Require normal draws to distinguish clockwise rotation from all seven other
  D4 transforms. Three demonstrations are declared; the schedule period is two.
- Reversed v2.0.0's belief that D4 and size-gated rivals sufficiently covered
  teaching risk. A crop-bounding-box/rotate/repad-top-left rival fit all four
  canonical pairs and all demonstrations of three retained lessons but changed
  their actual Racket query answers. See `counterexamples/crop_repadding.json`.
- Added 16 crop placements: start, floor center, ceil center, and end on each
  axis. Eight fit all canonical pairs. Default larger slots force one blank
  margin to exactly one and its opposite to at least three, with randomized
  orientation, position, and color. This refutes every crop placement.
- Keep that margin restriction out of exact override requests: a dense 4×4
  request remains feasible. The smallest default constrained interior has 15
  cells, sufficient for at most 12 marks. The lesson hook still diagnoses
  ambiguous override-built lessons; no universal override-curriculum claim is
  made.

Every four consecutive default pairs contain two larger witnesses, so a
three-demonstration lesson retains one after any single query holdout. There
are 24 unique declared rivals, not 57 distinct hypotheses merely because the
census reports the same functions in multiple declaration namespaces.

## Evidence and limits

Return `review-7f65e00a26f3126b` records: 12/12 final battery stages; 63/63
portable task tests; 19,440 exact-control tuples (14,337 feasible and 5,103
explicitly incompatible); 300 three-demonstration lessons and 1,200 query
rotations with no surviving tested ambiguity. Period-two enumeration covers
both starting residues at seed 0 in all three bands. Full commands, hashes,
failed iterations, and denominators are in that return's `RESULTS.json` and
`checks/`; `workspace/README.md` documents the reusable probe.

The strict teaching validator intentionally excludes monochrome, empty,
single-mark, dense, and malformed inputs even when rotation itself is defined.
Canonical-size slots couple size, mark count, and palette; larger slots impose
margin contrasts. This is a deliberately biased teaching distribution, not
uniform coverage or proof against undeclared rivals. No training approval is
changed by these checks.

The pending earlier audit `review-4955a8d54ae6bb80:v0001` was used as a lead,
then reproduced on the pinned v1.3.0 baseline. Its ignored-control findings are
addressed here. Its evidence index is intentionally unchanged: after integrating
this source, the maintainer should record the disposition against the retained
old-source audit. Unrelated audit targets and shared test failures are outside
this task delta.
## Current reviewer considerations

Source SHA-256: `b061470d1671eddf5ab1176e7d2cc650e77dca425318968459f52b20e377978d`.

# Decisions — review-7f65e00a26f3126b

## Assignment, authority, and scope

The immutable draw selected repair task `148acacd84d9`, question
`qwen9-data-value`, blind solve `2fd7d58a066c`, and subsequently audits
`3adf11522bf5` and `2d4e8c8fa10e`. Neither assignment was rerolled. The original
ZIP SHA-256 is `abe5d053b32d6dfa2a186f66af2106411df69af0836b69c2d94c030f92061821`.

The canonical rule rotates the whole canvas clockwise. Its normalized rule
SHA-256 is `2f0ece3d3c8fb4d1ab49e49b44111668a1bffc8676394da21b4495e0bbb47f7c`;
the declared pin is `2f0ece3d3c8f`. Racket source and canonical data are unchanged.
All production labels and retained audit/crop counterexample labels came from
the supported Racket interface. Independent Python geometry in tests computes
expected positions and rival predictions; it does not replace label authority.

Only the selected generator, its summary/notes, tests, workspace probe, and
counterexample are patched. Root frozen fixtures, shared source, prior evidence
indexes, and the two audit generators remain unchanged. The packet builder
checks this scope. Returned check reports and solve logs are review artifacts.

## Evidence stages and why the repair changed

| Stage | Generator SHA-256 | Meaning |
| --- | --- | --- |
| Before, v1.3.0 | `75bec50490ffae2f300f03a1a3d97a779387a780e9d658d6d43b7567c4a55421` | Pinned original; ignored controls, weak validation, absent teaching contract. |
| Intermediate, v2.0.0 | `24c18185e566588124a20506265cb886e2bec2977816bdfedc160a355baa8eac` | Exact controls and initial D4/size teaching repair; initially green but crop ambiguity remained. |
| Final, v2.0.1 | `b061470d1671eddf5ab1176e7d2cc650e77dca425318968459f52b20e377978d` | Adds the complete 16-placement crop family and default margin witnesses. |

`checks/before/` is baseline evidence. `checks/after/`, `checks/lesson-census.json`,
`checks/schedule-census.json`, and `checks/joint-controls-final.json` describe
the **intermediate** source, despite the latter's earlier filename. Final
evidence uses `checks/after-final/`, `checks/task-tests-final/`,
`checks/lesson-census-final.json`, `checks/schedule-census-final.json`, and
`checks/joint-controls-final-v201.json`. Exact intermediate generator bytes are
retained in `checks/intermediate-generator-2.0.0.py` to replay its failures.

The prior unresolved audit `review-4955a8d54ae6bb80:v0001` was a lead, not a
substitute for new measurements. Its retained return SHA-256 is
`731229493564678f4389e97ddce3c1ebb30a876f70b56289b9204aa56ac9a7ee`; its prior
probe SHA-256 is `b242dd3359d05c0e2c44c106434d432984204d419fd1044d44519613527cee3a`.
The selected task's existing evidence index identifies that return. Fresh
seed-123/index-4 observations in `checks/baseline-control-witness.json` reproduced
ignored size/palette controls and unknown-key acceptance. The existing index is
not a permitted patch target; the current notes request a maintainer disposition
after integration, without rewriting old evidence.

## R1 — truthful exact controls

The original generator advertised controls that did not affect the grid, with
unprobeable palette metadata and silent unknown-key acceptance. The original
intent behind those declarations is unknown. Retaining misleading aliases or
guessing their intended behavior would perpetuate an unreliable API.

The replacement exposes four exact integer controls: height/width 4..12,
foreground count 3..12, and total palette size 3..10. Palette size includes zero,
matching the independent pixel observer and shared checker convention. Every
nonzero color is used at least once. The default choices adapt to partial
overrides, so specifying a palette does not cause an avoidable mark-count
failure. Explicit palette greater than marks plus one has no feasible grid and
raises `ValueError` with `incompatible_axes`, backed by the declaration.

Unknown controls, removed corner/asymmetry/palette-kind controls, booleans, None,
and noninteger values fail clearly. Rejecting unsupported inputs is deliberate;
silently coercing them would make the exact contract ambiguous. Difficulty
changes sampling weights but does not narrow accepted override values.

The task-owned `workspace/probe_joint_controls.py` enumerates the complete four
axis product at seed 123/index 4 in all three bands. Baseline limited evidence
contains exact mismatches, feasible rejection, and undeclared infeasible
acceptance. Final evidence covers 19,440 tuples: 14,337 feasible draws, 5,103
structured incompatible rejections, 60 deterministic repeats, and no failures.
This is exhaustive over values at those parameters, not over all seeds. The
shared final override stage separately checked 524 cases and 47,160 draws with
30 seeds per case: 45,270 accepted, 1,890 explicit rejections, zero findings or
warnings. These denominators describe different probes and are not summed.

## R2 — domain and canonical support

The imported summary says square rotation, and all four canonical inputs are
squares. The previous default sampled mostly rectangles and the profile-floor
before report had only 5/60 exact hits, with no hard-band support. The repair
therefore uses squares by default, while preserving independently requested
rectangles as an explicit lawful extension. Square demonstrations do not prove
rectangular transfer; that limitation is now stated in the generator and notes.

Even sample indices draw side 4, 5, or 6 with canonical-like count and palette
profiles. The 5×5 slot now permits both four and five total colors; the 4×4 and
6×6 slots use four and five. Odd indices draw side 7..12, with band preferences
but nonzero support for the whole range. Both bands of size occur in every
difficulty. This intentionally couples default size/count/palette, rather than
pretending to offer a uniform product distribution. The independent exact
controls supply broader diagnostic coverage. The final profile-floor result
is 30/60 exact canonical size/palette hits: easy 9/20, medium 10/20, hard 11/20.

The normal validator is total and defensive: nonempty rectangular lists,
dimensions 4..12, true integer colors 0..9, zero background, 3..12 foreground
cells, at least two foreground colors, and non-noop rotation. Strict default
support also requires squares. Empty, single-mark and full-grid diagnostics
remain explicit named fixtures, outside AXES and outside normal teaching
validation. They are valid Racket inputs, not normal curriculum samples.
Helpful texture aliases that duplicated negative fixtures were removed.

## R3 — orientation and lesson assembly

Every normal draw must disagree with the other seven whole-grid D4 maps:
identity, counterclockwise rotation, half-turn, horizontal and vertical flips,
transpose and antitranspose. This excludes symmetric examples that cannot teach
orientation. It is an input-distribution constraint, not a change in the rule.

Three demonstrations are required. Four consecutive default pairs alternate
small and large squares with declared period two. The size-gated rival that
rotates only canonical sizes fits all four originals, so every lesson needs a
larger example. Two larger inputs per four-pair bundle let any one pair become
the query while retaining at least one demonstration that refutes that rival.
The remaining demonstration order is preserved. Production uses the first
three as demos and the fourth as query; required rotations hold out each once.

The shared random census used 100 lessons per easy/medium/hard band, requested
starts 0..99 and the recorded SHA-derived seed recipe, with 1,200 unique inputs.
It found zero ambiguous production lessons among 300 and zero ambiguous
rotations among 1,200. Its seed for every lesson is in the retained report.
The separate period enumeration used seed 0, starts 0 and 1, all bands: six
overlapping lessons, 24 rotations, only **five unique inputs**. This deliberately
small denominator exhausts declared start residues at one seed, not random
support. The focused tests also exercise starts 0..3 and all query exchanges.

## R4 — the initially missed crop/repad shortcut

The initial 8-rival repair passed the full battery and a 300-lesson census. An
independent review then found a plausible composition absent from that set:
crop the nonzero bounding box, rotate the crop clockwise, and repad at the top
left of the full output canvas. It fits all four canonical pairs and actual
v2.0.0 demonstrations at seed 4109, easy indices 228..230, yet differs from the
Racket query at 231. Medium and hard reproduce at demos 148..150/query 151.
The actual 16 Racket inputs (four originals plus three four-pair windows),
independent rival outputs, validation and command provenance are retained in
`checks/crop-repadding-before/` and the task counterexample fixture.

This disproved the sufficiency of the first repair even though its labels and
reported gates were correct. The nine-placement red regression had seven
failures and 54 passes: four insufficient-witness lesson tests and three old
wrong-query lessons falsely accepted by the hook. These failures were preserved.

The final rival family has four placements per axis: start, floor center, ceil
center and end. Both center conventions are needed for odd gaps. There are
16 distinct declared crop rivals, with exactly eight canonical-fitting ones;
the tests assert the whole declaration set and compare an independent geometry
oracle, including a fixture that separates the two center conventions.

Simply rejecting crop matches on every override draw was rejected as a repair:
dense 4×4/12-mark requests have too little free margin and could exhaust a
bounded sampler despite being feasible. Instead, default larger inputs use a
margin contrast: one side is exactly one, its opposite at least three, the
other pair at least one. A randomized near-edge mark makes the contrast real.
Rotation preserves this offset, while start/end/recentering loses it. This
refutes all 16 placements with a geometrical guarantee. The smallest constrained
interior has 15 cells, enough for the maximum 12 marks; sampling remains bounded
at 128 attempts and preserves exact palette/count observability.

This condition runs only for default larger samples with no override keys.
Even an override equal to a default value selects the exact-control branch;
that branch retains the D4 guarantee but not the crop teaching guarantee.
The public lesson hook can reject an ambiguous overridden lesson. The default
four-pair window still contains two crop-distinguishing large inputs, so every
single query holdout has a witness. Declared rivals total 24 unique functions
(7 D4 + 16 crop + 1 size). Declaration namespaces repeat them in reports; they
do not constitute additional hypotheses.

## Self-review of new restrictions

The repair introduces canonical-profile coupling, an even/odd size schedule,
and deliberate blank-margin contrasts; color identities, anchor direction and
positions remain randomized, and no output rule branches on those teaching
features. The independent review checked all 16 crop placements, odd centering,
the 15-cell capacity boundary and dense overrides; the final census supports
the declared finite rival claim but does not rule out new undeclared shortcuts
or establish uniform distributional coverage.

## Validation, infrastructure, and exposure

The final battery is 12/12 green with required rotations, 600/600 strict draws,
all four canonical inputs accepted, all three witness claims checked against
Racket, 12/12 smoke lessons and 48/48 rotations. Portable task tests explicitly
ran 63 cases with no failures, errors, or skips; they use public root/canonical
helpers instead of fixed parent-depth assumptions. Required final commands,
runtime paths, hashes, and clean-copy replay are recorded in `RESULTS.json`.

The first task-test attempt did not run tests: pytest existed only in the
normal interpreter's user site, while the portable runtime disables user-site
imports. That infrastructure failure is retained. A clean Python 3.12.14
environment with NumPy 2.5.3, Pillow 12.3.0 and pytest 9.1.1 passed the portable
stage. The initial whole-repository run had 11 failures, 548 passes and three
optional Torch skips; nine failures involved the same isolated prerequisite.
Two unrelated failures were independently reproduced before applying any patch
to a fresh extraction: historical-pair hash expectation for `defba1ab4f90`, and
an outdated unsupported-platform error-message regex. Neither shared source
nor frozen test was changed to silence these failures.

The first clean-environment repository run still had a third invocation-only
failure: its test compared a parent interpreter path containing `repo/..` with
the child's normalized path. Both the failure and a passing normalized version
were reproduced on the original packet; the decisive child output is retained.
The final normalized whole-repository run is **557 passed, 2 failed, 3 optional
Torch skips, 30 passing subtests**, exit 1. The two failures are the independently
reproduced baseline failures above, not a selected-task regression.

The exact 89,181-byte patch (SHA-256
`49f8a331c239a9d70f6d3adb87d56bfc6c4a43c6338619c0113046d3113a3b58`) applied cleanly
in that separate original extraction. All seven changed files matched the
candidate, and the public portable task stage passed all 63 tests again with
no skips. The candidate final and replayed generator bytes match the fresh solve.

The blind solve preceded generator/rule review and finished with 5/5 visible
examples on one candidate, earlier exposure no, reference consultation no.
The later fresh solve is honestly exposed: final source hash above, seed
638952274, three visible examples, two masked queries, one candidate, 3/3 visible
passes, earlier exposure yes and no reference consultation during that phase.
Both query correctness verdicts remain withheld. Logs are concise authored work
records, not claimed captured model conversations or probability traces.

## Audits and next maintainer actions

The two assigned audits are findings-only in `AUDIT.md`. Task `3adf11522bf5`
had no issue in 32 targeted generated draws, 36 public Racket executions, and
20 holdouts across four default windows. Task `2d4e8c8fa10e` has an orientation
support gap: a height-two/four-cell rival fits generated templates and canonical
pairs but fails a valid transposed query; this is not a wrong current production
label. Its maintainer should reconcile the broader validator domain with
generated tetromino orientations.

The highest-priority shared recommendation is F1, a canonical-compatible
crop/transform/repad family in lesson checking, using cached authoritative
labels and the declared query policy. The task-local implementation is included;
the shared change is a separate maintainer decision. No Qwen training experiment
or improvement estimate was performed. Passing checks and this return do not
alter training admission or catalog approval.

## 2026-10-24 native parametric relay review

This return leaves the production generator and canonical authority unchanged. It
adds a task-local native two-setting family under `workspace/parametric/`:

- `post_rotation="none"` returns the exact canonical source
  `(rule! (rotate-cw g))` byte-for-byte.
- `post_rotation="marker_relay"` first rotates the whole canvas clockwise,
  settles non-marker payload toward a unique color-9 marker on the rotated
  border, reads the resulting contact color, then repacks the first-settled
  grid toward absolute top for contact color 1 or absolute left for contact
  color 2. The marker remains fixed during both settles.

The alternate is a real A/intermediate/B composition. A changes the payload
layout and creates marker contact; the contact value selects B; B consumes the
first-settled grid. The retained 7x7 protected-Racket witness has A settle right,
produces contact color 1, then has B settle top. A wrong-intermediate program
keeps A but swaps 1 and 2, selects left, and changes the final output. Both A and
B visibly change the selected case.

The adapter supports independent 2..6 demonstration and 1..4 query requests,
with four queries in ordinary episodes. Inputs are setting-neutral and prefix
stable. Public projection exposes all demonstrations and exactly one input-only
query per turn, with no total-query hint; the first turn is byte-identical to
single-query use. The fourth query is a substantive 30x30 scene with 72 payload
cells and broad row, column, and color coverage.

Finite teaching evidence uses protected Racket only. Across both settings,
seeds 0 and 17, demonstration counts 2, 3, and 6, and four queries, the retained
self-audit ran 180 cached Racket evaluations. It found no claim mismatch and no
rival that fit the demonstrations while changing a query. The declared finite
rivals were the opposite setting, skip-A, skip-B, wrong order, wrong contact,
opposite second edge, always-top, and always-left. This is bounded evidence,
not universal identifiability.

Fresh verification retained in this return:

- 31 focused parametric tests passed.
- All 94 task tests passed.
- Native qualification passed both settings on seeds 0 and 17 with three
  demonstrations and four queries: four jobs, 40 protected-Racket evaluations.
- The causal witness was constructed and replayed through protected Racket.
- The current prototype inventory is source-bound in
  `workspace/parametric/evidence/manifest.json`.

Reviewer status is `ready`, not accepted. Owner integration must replay exact
live bytes, perform native acceptance, and separately decide whether any data is
admitted to training. Current `parametric status` remains `not_accepted`, and
`training_admitted` remains false.
