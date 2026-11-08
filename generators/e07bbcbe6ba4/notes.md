# Current notes: e07bbcbe6ba4

## Current state

- Version `4.0.0`; generator SHA-256
  `865e351f06fa59bc4fb29571572366f77f4a0867c3924391b4bca91aa07d2678`.
- Canonical `RULE_HASH`: `6c9f49f37571`; selected Racket source SHA-256
  `037ff6659c65492403f63da021ff422d16b36719afed937502aaf70fa93d8d02`.
- Selected `target_code` texts now exactly match the canonical source. The rule
  did not change; archival `raw_code` is preserved.
- Strict final battery: 12/12 green. Reviewer-owned focused tests: 26/26 green.
- Aggregate portable task-test status: blocked by an inherited frozen fixture's
  fixed parent-depth canonical path; do not interpret this as a failure of the
  new portable tests.

## Intended rule

The input has one complete color-3 rectangular frame and exactly one interior
color-3 marker. Preserve all 3s and all cells outside the frame. For each zero
cell strictly inside the frame, let
`d = max(abs(row-marker_row), abs(col-marker_col))`; output 2 when `d` is even
and 4 when `d` is odd.

## Public call and distribution

`seed` and `sample_index` are literal integers (bool is rejected), sample index
is nonnegative, and difficulty is `None`, `easy`, `medium`, or `hard`. Unknown
override keys and nonliteral geometry values reject loudly. Advertised exact
axes are `grid_h`, `grid_w`, `frame_h`, `frame_w`, and `marker_edge`.

Lawful grids span 9–30 rows/columns and frames span 7–24 rows/columns, with
band-specific ranges. Frames keep an exterior margin; the marker is strictly
inside and may be edge-adjacent or interior. With no geometry override, a 33%
prior emits the exact canonical 15×15 / 9×9 profile. This choice replaced a 30%
prior after a pinned census measured only 13/60 envelope hits; final support is
17/60 (easy 4, medium 9, hard 4).

## Semantic contract

All eight canonical labeled pairs share the same canvas and frame bbox, so the
plausible `fixed_canonical_bbox` rival fits them all. Variable frame/canvas
geometry refutes it. The rival is declared in `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; the witness is
`variable_geometry_refutes_fixed_bbox`. `lesson_identifiable` rejects a lesson
when the rival still fits every demonstration.

Final evidence: 600/600 strict semantic draws, witness 595/600, rival claim
60/60; 300/300 production lessons and 1,200/1,200 query rotations identifiable
with 1,137 unique inputs. These finite checks cover the declared rival and
sampler, not every possible induction hypothesis.

## Native parametric extension

`workspace/parametric/adapter.py` now exposes four episode-fixed settings:
`distance_metric={chebyshev,manhattan}` ×
`origin_mode={marker,nearest_wall_reflection}`. The default is the byte-exact
canonical source. Reflection first selects the input-dependent nearest wall,
moves the marker across that wall's axis, then runs the fill on the intermediate
grid. Skip-reflection changes ordinary painted cells as well as the marker.

The native contract supports 2–6 demos and 1–4 queries independently, defaulting
to 3/4 in the prototype. Inputs depend on seed/role/index rather than settings.
Two constructive demos expose both axes, opposite marker phases and equal
frame-center phases; a long second frame exposes distance caps. The prototype
rejects 13 declared rivals from demonstrations alone. The frame-center shortcut
was reproduced at seed 0 / Manhattan marker and seed 1 / Manhattan reflection;
equal center parity repairs both without another demo. The fixed-row reflection
shortcut has a separate executed two-demo counterexample and repair.

Four queries span 9×9, 21×23, 25×27 and 30×30 with frame sides 7–24. The largest
contains a 24×24 frame and 22×22 filled interior. Unique nearest walls are an
explicit shared input constraint; ties are excluded only from this parametric
sampler. Manhattan parity is equivalent to a marker-phased checkerboard.

Current source checks: 42 focused tests; 12/12 bounded requests with zero retries;
8/8 canonical pair replays; four retained 3-demo/4-query examples; 16 public files
with content-only IDs and one visible query each. Exact commands and failures
superseded by the repair are in `WORK/checks/e07bbcbe6ba4/`. The old files in
`evidence/retained/` remain inherited provenance; their setting-named public
exports are superseded. Use `evidence/current/` and the new projection helpers.
Owner qualification/acceptance of the exact integrated source remains mandatory.

## Known limits and open item

The family remains one axis-aligned frame, one marker, and fixed semantic
colors. The 300-lesson census is random production coverage, not exhaustive over
all seeds or undeclared rivals. The inherited aggregate canonical test blocker is maintainer-owned migration
of the frozen root test fixture to portable `reviewer_support` path helpers.
That unrelated aggregate suite was not rerun for this prototype-only change.
The native variant handoff is separately gated by owner exact-source acceptance.

## Current owner source and evidence limits

Accept strict typed allow-list and intentional version4.0.0 geometry expansion to9-30 canvases/7-24 frames. Add fixed-position/bbox rival and variable-geometry witness. Canonical Chebyshev rule unchanged;selected text normalization statically verified. Reviewer reports12/12 battery,26 focused tests,300 lessons/1200 rotations/1137 unique inputs clean,595/600 witness hits,17/60 exact profile. Aggregate task tests remain BLOCKED before discovery by unchanged frozen root fixture;focused tests are separate. Proposed Chebyshev/Manhattan episodes keep frame/marker reasoning,exact default canonical source,8/8 canonical parity. Prior unknown-key findings addressed by explicit allow-list/regressions. No fixture waiver or variant/training approval. Owner checked hashes and public/private structure statically; tests and labels remain reviewer-reported.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0bb5cf551818a26c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9edcd6313c6ccd7ac5b979eb6b3c9cefe507ba712bc477d762fea86f217aa6d8`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolve repeated exact unknown-control finding. Accepted865e351f source checks set(overrides)-allowlist before GenCtx;26 focused regressions and final override gate report rejection of misspellings. Canonical Racket unchanged. Frozen aggregate task fixture remains separately blocked;not a waiver or broad semantic certification.

### Assessment or prior finding

## e07bbcbe6ba4

**Reproduced defect — unknown override keys are silently accepted.** The audited source SHA-256 is `9edcd6313c6ccd7ac5b979eb6b3c9cefe507ba712bc477d762fea86f217aa6d8`.

Calling `generate(0, 3, difficulty="easy", __override_contract_unknown_axis__=123)` returns an 11×13 grid and `self_check` returns no errors. A misspelled, removed, or renamed control can therefore appear successful while changing nothing. The compact reproducer and output are:

- `checks/audit/e07bbcbe6ba4/reproduce_unknown_override.py`
- `checks/audit/e07bbcbe6ba4/reproduction.json`

The official override audit independently reports exactly one minimized unknown-key finding in `checks/audit/e07bbcbe6ba4-override/result.json` after 42,930 draws. No files for this audit-only target were modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-0bb5cf551818a26c-v0001/audit_assets.json), manifest SHA-256 `7c65d9a61d6c63453aec6134e87c4ecfc97c6f42d67096b2237bd77ef511f004`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `865e351f06fa59bc4fb29571572366f77f4a0867c3924391b4bca91aa07d2678`.

# Decisions for e07bbcbe6ba4

## D1 — Preserve the canonical transformation and rule pin

**Choice.** Keep the color roles and Chebyshev ring rule unchanged. The frame
and marker remain color 3; interior zero cells become 2 for even Chebyshev
distance and 4 for odd distance. `RULE_HASH=6c9f49f37571` stays pinned.

**Rationale.** The defects were request validation, authority text drift,
distribution support, and teaching identifiability—not incorrect canonical
semantics. Changing the production rule would invalidate the original-family
identity and conflate repair with variant authoring.

**Rejected alternatives.** I rejected changing colors, adding distractor
objects, or switching production to Manhattan distance. Those either reskin the
same task or change the authority. Manhattan remains separate as a proposed
prototype.

## D2 — Reject malformed public requests before keyed drawing

**Choice.** Validate `seed`, `sample_index`, `difficulty`, and override keys in
one entry-point helper. Seeds and indices must be literal integers (not bool,
float, or string); sample index must be nonnegative; difficulty must be
`None/easy/medium/hard`; geometry axes must be literal integers in declared
domains; `marker_edge` accepts a bool or the explicit strings `true/false`.
Unknown override names raise immediately.

**Rationale.** Silent coercion and ignored misspellings destroy exact replay and
make audits misleading. Validation must happen before RNG/context drawing so a
bad request has no hidden side effects.

**Failure probes.** `test_review_repairs.py` includes booleans, floats, strings,
negative indices, bogus difficulty values, misspelled axes, and nonliteral
geometry values. The public override matrix then checked 4,770 combinations.

## D3 — Expand actual frame geometry, not merely background padding

**Choice.** Use grids 9–30 and frames 7–24, with band-specific ranges and
compatible exact overrides. Both frame dimensions, canvas dimensions, and
marker edge/interior placement vary.

**Rationale.** Longer frames create additional rings and clipped/asymmetric
patterns, exposing the true distance relation. Enlarging only the zero margin
would add visual variation without changing the reasoning evidence.

**Rejected alternatives.** I rejected fixed 9×9 frames on variable canvases and
fixed-position frames. Both preserve the strongest canonical shortcuts. I also
rejected arbitrarily huge grids because they add runtime and token cost without
new local rule structure.

**Limits.** The generator still deliberately uses one rectangular frame, one
interior marker, colors `{0,2,3,4}`, and axis-aligned geometry. Those are family
constraints, not a universal claim about all possible ring tasks.

## D4 — Retain exact canonical support with a measured 33% prior

**Choice.** When no geometry override is supplied, use a 33% exact canonical
profile prior (15×15 grid, 9×9 frame), then sample the expanded band domain.

**Rationale.** A 30% prior failed the pinned public census at 13/60 envelope
hits. A test was added first; 33% gives 17/60 on the final source (4/20 easy,
9/20 medium, 4/20 hard), satisfying every band and the pooled 25% floor while
leaving most draws variable.

**Rejected alternatives.** I rejected forcing canonical geometry in half or all
draws because it would weaken the variable-geometry witness. I rejected tuning
to exactly 15/60; 33% is a small round adjustment with modest stochastic
margin, not a hand-selected per-band schedule.

## D5 — Model the strongest canonical shortcut explicitly

**Choice.** Declare `fixed_canonical_bbox`: assume a 15×15 input with frame bbox
rows 2..10 and columns 3..11, and otherwise leave the grid unchanged. Bind it in
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`. Declare the
variable-geometry witness and make `lesson_identifiable` reject lessons whose
demonstrations all fit the rival.

**Rationale.** Every usable canonical pair has the same canvas and frame bbox,
so the rival genuinely fits all eight labeled pairs. It is stronger and more
plausible than an arbitrary memorized output because it applies the intended
local rule only at the canonical location.

**Probe.** The exact 9×9 / 7×7 witness generated by seed 9, sample index 3
passes `self_check`; protected Racket and the independent mirror agree, while
the rival returns the unchanged input. See the retained counterexample JSON.

**Limits.** Refuting one declared rival does not prove unique induction. The
300-lesson/1,200-rotation census is finite and samples the production schedule;
it does not enumerate every seed or undeclared hypothesis.

## D6 — Synchronize selected executable authority, preserve archives

**Choice.** Apply the checker-generated proposal to the two selected
`racket_target.target_code` fields so they are byte-for-byte equal to the
canonical program. Preserve both `raw_code` fields unchanged.

**Rationale.** Exact source binding should identify one selected executable
program. The drift was formatting-only, and execution parity already passed;
there was no justification to rewrite archival source or change `RULE_HASH`.

**Evidence.** Final selected files hash to
`1fab733e3acf7ff9a9656924d52b0bd40bfacd9f13ce3c54b9e57d3bd1cccc33`
and `91a0dbdaf60acc7b7290f4a0a9756bc94feae2f425e2962de2e45f29a09f22ce`.
The final authority gate reports selected synchronization, preserved archival
divergence, and execution parity PASS.

## D7 — Native distance/origin family, canonical authority unchanged

**Current choice.** Replace the fixed 3-demo/1-query prototype with the native
four-setting family described above. Reuse the pinned metric materialization;
compose marker relocation only for the alternative origin. Preserve canonical
generator and reference bytes. Three demos remain the default, while the first
two constructively reject the finite rivals. Public files now hash visible bytes
and expose one query at a time; settings and ordering stay in private records.

**Reason for reversal.** The earlier fixed fixtures, one query and metric-named
public filenames did not satisfy native promotion or sequential-reveal duties.
Nearest-wall relocation provides a real intermediate grid the fill consumes.
The prototype remains subject to exact-source owner acceptance and downstream
training decisions; local qualification does not grant either.

## D8 — Do not edit the inherited frozen fixture

**Choice.** Leave `tests/test_generator_e07bbcbe6ba4.py` byte-for-byte unchanged
and add portable regressions in separate files.

**Rationale.** The assignment explicitly assigns frozen-fixture migration to
the library maintainer. Editing it would hide a real portability defect and
violate packet scope. New tests use the supported reviewer helpers and pass in
the repository layout.

**Consequence.** The canonical repair is fully verified, but aggregate portable
task-test completion remains `blocked` until the maintainer migrates that
fixture.
