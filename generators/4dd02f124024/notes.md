# Working notes: 4dd02f124024

## Review scope and source identity

Assignment `review-624525eef99da2e9` selected generator `4dd02f124024` at SHA-256
`d34f0b6f57b84c9c27fdc46ba81f644313d322470c94f04a45b661e51f2e4850`
(version 1.3.0). I used the unresolved prior audit in
`evidence/review_index.json` (`review-e7912a4265cfdbc9:v0001`) only as a lead.
That audit's no-op palette witness was rechecked against the immutable selected
source; all conclusions below come from this packet's source and retained checks.

The canonical transformation and selected Racket authority were not changed.
The final generator pins canonical `RULE_HASH = "1ded33eac0b5"` and has SHA-256
`7132022847bd5b3b9059ee33a52ced1416673a5061b82e04acd7ec20cbff1be9`.

## Baseline findings

The before battery (`checks/before/`) finished with 7 green, 2 advisory, and 3
failed stages. Lint failed because `RULE_HASH` was absent. Defect lint and the
override contract found a wide, misleading control surface: `palette_kind` was
a reproducible no-op, several axes were singleton/dead, unknown and malformed
requests were not rejected consistently, and degenerate texture paths did not
honor the grid contract. Profile-floor support was weak, especially in the hard
band. There was no task-linked strict predicate, executable rival set, or
lesson-level identifiability hook.

A deeper curriculum defect was visible after comparing canonical and generated
support. Canonical examples fit two plausible shortcuts:

- erase only the foreign-colored cells rather than every occupied interior cell;
- process only the first mismatching frame.

Baseline generated mismatches also used only foreign cells, so they did not
force a learner to erase own-color cells after a foreign trigger. Lessons with
one mismatch did not refute the first-mismatch-only shortcut.

## Final design

Version 2.0.0 replaces the nominal eight-axis surface with five exact controls:

- `grid_h`: 9..17
- `grid_w`: 14..20
- `n_frames`: 2..4
- `palette_kind`: `default|warm|cool|varied`
- `interior_style`: `foreign_only|sparse_mixed|dense_mixed`

Every legal joint override is constructive and observable. Inputs contain two
to four separated rectangular frames in fixed quadrants, distinct frame colors,
and a shared foreign trigger color. At least one frame matches and at least one
mismatches. With three or four frames, mismatch indices 0 and 2 ensure more than
one bad frame.

The default curriculum cycles over five profiles:
`canonical_9x14`, `mixed_10x15`, `mixed_9x16`, `mixed_10x16`, and
`extended_12x18`. Every four-example cyclic window contains mixed own/foreign
interiors and a multiple-mismatch example. The schedule remains in
`SCHEDULE_PROFILES`; exhaustive task tests cover all five cyclic starts in all
bands and hold out every pair as query.

`foreign_only` retains sparse canonical-like support. `sparse_mixed` stamps one
own-color cell plus one foreign trigger. `dense_mixed` uses a full checkerboard
of frame and foreign colors. The latter choice is deliberate: a solid or
monochrome dense interior can itself form a nested rectangular frame under the
canonical scanner.

The module now provides:

- strict request validation and `observe_overrides`;
- structural frame analysis and `strict_canonical_like`;
- an independent Python rule mirror checked against all canonical labels;
- executable witnesses and rivals (`identity`, `erase_all_interiors`,
  `erase_only_foreign`, `first_mismatch_only`);
- canonical-fitting shortcut declarations;
- `lesson_identifiable` for four-demo lessons and each query.

## TDD and failed iteration retained

The first regression asserted that warm and cool palette requests must change
pixels and round-trip through the observer. It failed on the selected baseline
for the intended reason: both requests returned the same grid. Production code
was then replaced around the new constructive contract.

An intermediate semantic run found a more subtle failure. A dense monochrome
interior could create nested uniform-border rectangles. Because the Racket rule
scans rectangles sequentially, an inner frame could erase the foreign trigger
before the outer frame was judged; the resulting label accidentally agreed with
`erase_only_foreign`. That failure is retained in
`checks/focused-semantic/`. A regression now scans 240 mixed-style draws for
nested-frame shortcut behavior. Sparse mixed examples use only two cells, and
dense examples use a checkerboard with no monochrome edge of length three.

A later strict battery had 11 green stages and a semantic warning solely because
`LESSON_SCHEDULE_PERIOD` was declared. The semantic tool emits that warning for
any positive declaration even when a separate exact-period census succeeds.
The warning run is retained in `checks/after/` and the clean schedule census in
`checks/schedule-census.json`. The final source keeps the five-profile schedule
and exhaustive cyclic-start tests but omits that public metadata constant; this
workaround is reported as shared-tool feedback rather than hidden.

## Final verification

Final-source generator SHA-256:
`7132022847bd5b3b9059ee33a52ced1416673a5061b82e04acd7ec20cbff1be9`.
Task-test SHA-256:
`5a06dcdeff0d84edb40b5ca8212cc1877ba3132a9d6bca538eabde89aa8e454f`.

- Full battery: 12/12 green (`checks/after-final/`).
- Task-local tests: 457 passed (`checks/task-tests-final/`).
- Override audit: 25,650/25,650 accepted draws, 285 cases, three bands, zero
  findings (`checks/after-final/checks/4dd02f124024_after_override.log`).
- Strict semantic gate: 600/600 strict draws, 4/4 canonical inputs, 3/3
  witnesses, 3/3 rival claims, 12/12 four-demo lessons, and 0/60 ambiguous
  query rotations (`checks/final-semantic/`).
- Production census: 300/300 materialized four-demo/one-query lessons, 1,500
  labelled pairs, zero production ambiguities, 1,500 required query rotations
  with zero ambiguities, and 1,485 unique inputs (`checks/lesson-census-final.json`).
- Post-repair visible-only solve: 4/4 visible examples on the first checked
  revision, bound to the final generator hash; prior exposure was disclosed and
  no reference/private labels were consulted during the solve (`solve/`).

## Remaining limits

The finite rival set and sampled census do not prove unique induction against
all possible programs. The five-profile cycle is intentionally structured, and
query rotations were checked because this packet's downstream assembly allows
them. The rule authority is unchanged; this repair improves sampling,
contract honesty, and teaching support only.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e7912a4265cfdbc9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d34f0b6f57b84c9c27fdc46ba81f644313d322470c94f04a45b661e51f2e4850`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

No-op palette_kind/missing rule pin/profile support finding on d34f0b6f57b8 addressed by accepted624525 source7132022847bd: unsupported nominal axes replaced by5strict observable controls, RULE_HASH1ded33eac0b5, constructive five-profile curriculum. Reported457 regressions,12/12 battery,25650override draws0findings and300lesson/1500rotation census; no independent rerun or universal support claim.

### Assessment or prior finding

## 4dd02f124024

**Reproduced defect — advertised override is a no-op.** Generator SHA-256:
`d34f0b6f57b84c9c27fdc46ba81f644313d322470c94f04a45b661e51f2e4850`.
At seed `0`, sample index `0`, difficulty `medium`, both
`palette_kind="warm"` and `palette_kind="cool"` are accepted, pass
`self_check`, and produce the byte-identical grid SHA-256
`6456096b278d2f5bf8f46beac0ba4f501a8ebb73ba824996f057a4258a85bf43`
with the same nonzero palette `[2, 3, 6]`. Full grids and invocation metadata are
retained in `checks/audit/4dd02f124024/override_noop.json`.

This is inside the documented generator domain and falsifies the advertised
`palette_kind` control, though it is not a Racket-label counterexample. The
official override stage also failed with many contract findings; the linter
reported a missing `RULE_HASH`, and the profile floor found only 3/60 exact
canonical profiles with zero hard-band support. Evidence is under
`checks/audit/4dd02f124024/`. No fix was made.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e7912a4265cfdbc9-v0001/audit_assets.json), manifest SHA-256 `cd625935e3ce75140edc7ea6eb6b03974e4c5bd4901e1948676e33815606ea4d`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `7132022847bd5b3b9059ee33a52ced1416673a5061b82e04acd7ec20cbff1be9`.

# Decisions for 4dd02f124024

## D1. Preserve the canonical Racket rule

**Choice.** Do not modify canonical or base authority; pin
`RULE_HASH = "1ded33eac0b5"` and test a Python mirror against every canonical
pair.

**Why.** All canonical labels and both executable authorities agree. The defect
was in generation and teaching support, not label semantics.

**Rejected.** Rewriting the sequential rectangle scanner to simplify nested
behavior. That would change the task rather than repair its curriculum.

**Probe.** Final authority sync, 120-rule-smoke mirror comparisons, and canonical
parity task tests.

## D2. Replace the misleading axis surface instead of patching each old knob

**Choice.** Expose exactly five controls: `grid_h`, `grid_w`, `n_frames`,
`palette_kind`, and `interior_style`.

**Why.** The old surface mixed no-ops, singleton diagnostics, aliases, and
invalid degenerates. A smaller exact product is more useful for data generation
than a large nominal one.

**Rejected.** Preserve every old name with compatibility exceptions. That would
keep a difficult-to-audit contract and encourage callers to rely on controls
that do not correspond to pixels.

**Probe.** Final override matrix: 25,650/25,650 accepted draws, 285 cases, three
bands, no findings.

## D3. Use constructive quadrant slots

**Choice.** Place two to four frames in separated quadrants with at least one
blank row and column between regions.

**Why.** This makes joint dimensions/frame-count overrides feasible without
retry-heavy packing and prevents accidental overlap between intended frames.

**Rejected.** Free random packing with retries. It creates size-dependent
rejection bias and makes exact joint overrides fragile.

**Limitation.** Spatial arrangement is structured. Frame rectangles still vary
within slots, and the five profiles cover all canonical shapes plus a larger
12x18 case.

## D4. Share one foreign trigger color but keep frame colors distinct

**Choice.** Each frame has a distinct border color; mismatching frames use one
shared foreign color selected by palette family.

**Why.** Equality to the local border—not absolute color identity—remains the
only semantic cue. A shared trigger makes the cross-frame comparison visible
without creating extra arbitrary roles.

**Rejected.** A unique foreign color per frame, which adds unnecessary palette
entropy and can turn color identity into a frame-index cue.

## D5. Add mixed interiors that erase own-color cells

**Choice.** `sparse_mixed` contains one border-colored interior cell and one
foreign trigger; `dense_mixed` alternates both colors throughout the interior.

**Why.** Canonical pairs and old generation admit the plausible shortcut
“erase only foreign cells.” Mixed interiors provide the minimal prediction
where that shortcut differs from the authority.

**Rejected.** More foreign-only examples. They increase volume but not semantic
information.

**Probe.** Task tests assert own-color erasure, canonical shortcut fit, and rival
refutation in every cyclic lesson window.

## D6. Put two bad frames in examples with at least three frames

**Choice.** Mismatch frame indices 0 and 2; all remaining frames match.

**Why.** Canonical examples have one mismatch each, so “process only the first
mismatch” fits them. Two separated mismatches refute it directly while retaining
a positive frame.

**Rejected.** Make every frame mismatching. That would refute first-only but
allow “erase all interiors” and remove the positive condition.

## D7. Use a five-profile curriculum and test every cyclic start

**Choice.** Cycle canonical, sparse mixed, dense mixed, varied mixed, and extended
profiles. Four demonstrations are required; task tests enumerate all five start
residues in every band and rotate each of five pairs into query position.

**Why.** Any four consecutive profiles include mixed-content and multiple-
mismatch support. This gives deterministic teaching guarantees while preserving
layout variation from keyed draws.

**Rejected.** Fully random profile selection. It can produce a locally correct
batch in which a canonical-fitting shortcut survives by chance.

**Limitation.** The random production census samples starts rather than proving
all layout seeds. The task test exhausts cycle positions, not every geometry.

## D8. Use checkerboards for dense mixed interiors

**Choice.** Fill the complete interior with an alternating frame/foreign
checkerboard.

**Why.** The first dense implementation formed nested monochrome rectangular
frames. The sequential Racket scanner could consume the trigger before judging
the outer frame. A checkerboard is dense but has no monochrome edge of length
three, preventing that causal interference.

**Rejected.** Post-filter only the intended outer frames in the Python mirror.
That would hide a real difference from the authoritative scanner.

**Probe.** Retained failing semantic report in `checks/focused-semantic/` and 240
nested-frame regression cases in the final test suite.

## D9. Keep strict input and request validation

**Choice.** Reject unknown axes, invalid override types, negative or noninteger
sample indices, malformed/ragged grids, booleans as cells, and unrealizable
frame structures.

**Why.** Silent coercion and ignored metadata make source-bound data audits
unreliable. Every accepted request must have a deterministic, observable result.

**Rejected.** Let `GenCtx` coerce strings/floats for convenience. That makes
call-site mistakes indistinguishable from intentional requests.

## D10. Declare and execute plausible rivals

**Choice.** Provide identity, erase-all, erase-only-foreign, and first-mismatch-
only rivals; separately mark the two that fit every canonical pair.

**Why.** Pixel validity and correct labels do not establish a teachable lesson.
Executable rivals allow the semantic gate and lesson census to ask whether the
demonstrations actually distinguish the intended transformation.

**Rejected.** Witness-frequency checks alone. A witness can be present yet
redundant if it does not change any rival prediction.

## D11. Do not publish `LESSON_SCHEDULE_PERIOD` until the shared gate can consume its census

**Choice.** Retain `SCHEDULE_PROFILES` and exhaustive five-start task tests, but
omit the public period constant.

**Why.** The strict semantic battery emits a warning for any positive period
and cannot consume the clean source-bound schedule census, making an otherwise
green final battery fail policy.

**Rejected.** Suppress or ignore the warning in the report. The return must be
routinely replayable under the packet's strict policy.

**Limitation.** Shared tooling cannot automatically discover that the period is
five. `FEEDBACK_TO_CODEX.md` proposes a source-hash-bound schedule-census receipt
or in-gate period enumeration.
