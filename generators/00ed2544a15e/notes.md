# Working notes: 00ed2544a15e

## Review identity

- Assignment: `review-feb9c8cb558d5d22`
- Baseline generator SHA-256: `ad6adde479bf304847f13ce650f47ddb7cc144be0efa93238b4c30866b2174f1`
- Final generator SHA-256: `5556b7cf1d2bf1b2f59ff5a0abfc12c97eeeb511a381e1bf47fe1d549e8bf01b`
- Canonical rule hash: `92ea0e00d9a5`
- No prior return was used as a lead; `evidence/associated_notes.jsonl` was empty.
- Racket semantics changed: **no**. One archival `target_code` comment was removed
  so selected, canonical, and raw authority sources are byte-identical.

## Canonical rule understood

Find every unordered pair of red (`2`) cells sharing a row or column. Paint the
strict interior cyan (`8`) exactly when the original inclusive segment contains
only black and exactly those two red cells. A third red suppresses an outer span;
a non-`{0,2}` color blocks that span. Eligibility is computed from the original
input, so overlapping valid subsegments can share endpoints.

## Baseline findings

The required before battery finished with 6 green, 2 advisory, and 4 failed
stages (`checks/before/checks/00ed2544a15e_before_battery_summary.json`).

- `RULE_HASH` was absent.
- The selected archival `target_code` differed from canonical/raw authority by a
  comment, so exact authority synchronization failed despite execution parity.
- The rejection sampler advertised dimensions, pair counts, and textures that
  many difficulty bands could not realize.
- Degenerate textures were ordinary axis values even though they produced
  no-op or structurally invalid examples.
- Unknown override keys were silently accepted and no exact override observer
  existed.
- The strict override audit recorded 9,151 findings and 2 warnings over 106,020
  draws; 72,450 draws were explicit rejections and only 31,200 were accepted.
- No executable rival/lesson contract established that generated demonstrations
  teach blocker behavior or chain/shared-endpoint behavior.

## Repair

Version `3.0.0` replaces rejection sampling with three constructive local
profiles placed inside exact requested dimensions:

1. `h_chain`: a three-red horizontal chain, a clear vertical connection, a
   blocked vertical span, and an isolated red;
2. `v_chain`: the transposed semantic emphasis;
3. `cross`: horizontal and vertical arms sharing a center, with one blocked arm.

Each profile independently exercises both orientations, blocker behavior,
isolation, and a topology that refutes the canonical-fitting
`simple_pairs_only` shortcut. Profiles cycle by `sample_index`, while reflections,
offsets, dimensions, blocker color, and attached distractor shape vary
replay-deterministically.

The ordinary axes are now only:

- `grid_h`: every integer 8..12;
- `grid_w`: every integer 9..13;
- `profile`: `h_chain|v_chain|cross`.

Unknown or malformed controls fail loudly. `observe_overrides` recovers all
three exact controls. Medium/hard distractors extend the existing blocker-color
component rather than creating extra objects; this preserves a same-color
component count of 7, exactly at the inherited canonical detector's allowed
median envelope, while retaining semantic counterexamples.

Executable diagnostics now include:

- a Python mirror pinned to the selected Racket source;
- five lesson competitors: identity, horizontal-only, vertical-only,
  ignore-blockers, and simple-pairs-only;
- two verified canonical-fitting shortcuts: ignore-blockers and
  simple-pairs-only;
- six semantic witnesses plus witness-to-rival claims;
- `strict_canonical_like`, `schedule_profile`, `observe_overrides`, and
  `lesson_identifiable`.

## Test-first chronology

1. Added focused regressions before replacement. Against the inherited source,
   39 failed and 5 passed (`checks/tdd-red/`).
2. Implemented the constructive profiles; 44 tests passed
   (`checks/tdd-green-1/`).
3. Fixed default-profile provenance exposed by the strict override checker.
4. The first full after battery reached 11/12 green but defect lint showed
   generated same-color object counts 9..11 against canonical median 5
   (`checks/after-intermediate-component-failure/`).
5. Added a color-sensitive component-envelope regression, observed it fail, then
   reduced/attached template components; 45 tests passed and defect lint turned
   green (`checks/tdd-red-color-components/`,
   `checks/tdd-green-color-components/`).
6. Added the reusable curriculum probe test before its implementation; the red
   run failed on the missing tool, then the final task suite reached 46 passed
   (`checks/tdd-red-probe/`, `checks/tdd-green-probe/`).

## Final evidence

- Full required after battery: 12/12 green, no advisory/failure/interruption
  (`checks/after/checks/00ed2544a15e_after_battery_summary.json`).
- Semantic gate: 600/600 strict draws, all 5 canonical inputs accepted, 12/12
  lessons identifiable, every declared profile present.
- Rule smoke: 120/120 fired, 120 distinct outputs, 0 mirror mismatches, 0 input
  mutations.
- Override gate: 6,210/6,210 accepted draws, 0 findings, 0 warnings, unknown
  keys rejected.
- Profile floor: exact canonical-profile hits in every band, 26/60 overall.
- Diversity: 300 pairs, 98% unique inputs and outputs.
- Shared lesson census: 300/300 lessons materialized, 1,200 pairs, 1,117 unique
  inputs, 0 ambiguous lessons, and 0 ambiguous query rotations
  (`checks/lesson-census-summary.json`).
- Task-local tests: 46 passed (`checks/task-tests/` after final replay).
- Authoring probe: all 300 legal joint override cases, all 12 cyclic windows,
  every query rotation, and 100 deterministic sampled inputs passed; both
  canonical shortcuts fit 5/5 canonical pairs and have exact generated
  counterexamples (`checks/curriculum-probe.json`).

## Remaining limits

The finite rival set does not prove universal identifiability. Constructive
examples intentionally use three recognizable topologies and a constant seven
same-color object count; reflections, offsets, dimensions, colors, and attached
distractors provide variation, but future work could add more lawful topology
families without weakening lesson guarantees. The Python mirror is diagnostic;
the synchronized Racket source remains authoritative.
## Current reviewer considerations

Source SHA-256: `5556b7cf1d2bf1b2f59ff5a0abfc12c97eeeb511a381e1bf47fe1d549e8bf01b`.

# Design decisions: `00ed2544a15e`

## D1. Preserve the canonical rule; repair distribution and authority identity

**Choice.** Keep the Racket algorithm unchanged, pin its normalized hash, and
remove only the extra archival comment that caused exact source divergence.

**Rationale.** Rule smoke already showed correct execution, while authority sync
showed source identity—not semantics—as the defect. Rewriting a correct rule
would increase risk and erase useful provenance.

**Alternatives rejected.** Treating comment-only divergence as harmless would
leave a required gate red. Replacing all authority copies from one source would
be broader than necessary.

**Limit.** Byte identity does not by itself prove semantics; final execution
parity and canonical solves provide that separate evidence.

## D2. Replace rejection sampling with construction

**Choice.** Build legal examples directly from small semantic templates, then
reflect, offset, color, and attach safe distractors.

**Rationale.** The old sampler advertised domains it could not realize under
band-specific constraints and spent most audit draws rejecting requests.
Construction makes exact controls total and makes semantic witnesses causal.

**Alternatives rejected.** Narrowing each difficulty to whatever the old sampler
happened to accept would preserve hidden band aliases. Increasing retry counts
would waste work without fixing unreachable combinations.

**Failure mode guarded.** Every generated grid is post-checked against its
expected profile and teaching contract before return.

## D3. Keep only honest, observable axes

**Choice.** Expose dimensions and profile only: `grid_h=8..12`, `grid_w=9..13`,
and `h_chain|v_chain|cross`.

**Rationale.** Pair counts and texture labels in the inherited generator mixed
semantic, degenerate, and band-dependent behavior. The retained axes correspond
to visible properties recoverable from one grid.

**Alternatives rejected.** Keeping legacy names as aliases would complicate
provenance and perpetuate silent no-ops. Negative/no-op textures belong in
mutation fixtures, not ordinary generation.

## D4. Make every single example pedagogically sufficient against named rivals

**Choice.** Each profile contains clear horizontal and vertical spans, a blocked
aligned span, an isolated red, and a chain or shared endpoint.

**Rationale.** Depending on a particular three-example window is fragile under
query rotation and shifted starts. Per-example coverage means every cyclic
lesson and every held-out query still distinguishes the named rules.

**Alternatives rejected.** One profile per semantic branch would produce shorter
examples but require schedule assumptions downstream. Pure random pair layouts
could miss rare blocker/chain interactions.

**Limit.** Sufficiency is measured only against the executable rival set.

## D5. Rotate three topology profiles

**Choice.** Cycle `h_chain`, `v_chain`, and `cross` by `sample_index`.

**Rationale.** These are the smallest distinct structures that demonstrate
adjacent subpairs in a three-red line and a shared endpoint across orientations.
The cycle is easy to exhaust and audit.

**Alternatives rejected.** A single universal template would create stronger
layout leakage. A large randomized grammar would make exact semantic and
morphology guarantees harder to prove in this repair.

## D6. Retain two canonical-fitting shortcuts explicitly

**Choice.** Declare `ignore_blockers` and `simple_pairs_only` in
`CANONICAL_SHORTCUTS`; keep orientation-only and identity rivals in the broader
lesson set.

**Rationale.** Direct measurement shows the two shortcuts fit 5/5 canonical
pairs, so canonical demonstrations alone cannot reject them. They are the
highest-value new teaching obligations.

**Alternatives rejected.** Calling every wrong rule a canonical shortcut would
make the contract meaningless. Omitting them would let a lesson be label-correct
but inductively ambiguous.

## D7. Compute eligibility from the original input

**Choice.** The Python mirror and inferred solve enumerate pairs against the
unmodified source grid, writing cyan only to a copy.

**Rationale.** Painted cells from one span must not create, block, or alter the
eligibility of another span. This matters for chains and shared endpoints.

**Alternatives rejected.** Sequential in-place scans are order-sensitive and can
silently change overlapping behavior.

## D8. Use one blocker color and attach difficulty distractors to it

**Choice.** Medium/hard variation grows the existing blocker-color component in
safe rows/columns rather than adding independent objects.

**Rationale.** The first constructive draft had 9–11 same-color objects, outside
the inherited canonical median tolerance. Attaching cells preserves blocker
semantics and variation while holding the object metric at seven.

**Alternatives rejected.** Deleting all distractor variation would make bands
identical. Adding more red markers risks accidental relations. Adding isolated
colors recreates the morphology defect.

**Known restriction.** Object count is now constant. This is explicit and
preferable to drifting outside canonical support; future families can broaden it
under a tested envelope.

## D9. Weight ordinary dimensions toward canonical profiles while supporting all boundaries

**Choice.** Duplicate common height/width values in the default choice lists,
but allow every declared exact value in every band.

**Rationale.** This yields nonzero exact canonical profile support without lying
about the legal domain or rejecting boundary requests.

**Alternatives rejected.** Fixed canonical dimensions would reduce shape
coverage. Uniform dimensions lowered canonical profile frequency for no semantic
benefit.

## D10. Validate controls and fail loudly

**Choice.** Reject unknown difficulty, unknown keys, booleans/non-integers, and
out-of-range dimensions/profile names before generation.

**Rationale.** Silent acceptance turns typos into mislabeled data. Exact failure
messages are cheaper than downstream provenance debugging.

## D11. Add strict manifold and teaching checks separately

**Choice.** `strict_canonical_like` checks broad lawful task structure;
`_teaching_contract_errors` additionally requires every ordinary example's
specific witnesses and rival disagreements.

**Rationale.** Canonical examples need not contain every new training witness,
so a validator that conflates lawfulness with curriculum requirements would
reject valid canonicals.

## D12. Test first and preserve decisive failures

**Choice.** Add regressions before each behavior change, retain red runs, and
keep the first failed after battery.

**Rationale.** The red runs establish that tests detect inherited defects rather
than merely restating the implementation. The intermediate defect-lint failure
caught a distribution issue not covered by the first semantic suite.

## D13. Build a live-declaration curriculum probe

**Choice.** Retain `workspace/curriculum_probe.py`, with its own test, and read
rivals/schedule directly from the generator.

**Rationale.** Copied name lists become stale. Future edits can rerun one fast
command to test canonical fit, all cyclic starts/rotations, exact axis support,
replay, morphology, and exact shortcut witnesses before expensive Racket checks.

**Limit.** The probe uses the Python mirror. The full battery/census remain the
Racket authority evidence.

## D14. Stop after all required gates and finite rival census were green

**Choice.** Do not add further topology families in this return.

**Rationale.** The repaired source passes all required gates, 46 regressions, the
300-lesson census, and fresh solve. Additional breadth would be a new design
cycle with new shortcuts and morphology risk, not a necessary bug fix.
