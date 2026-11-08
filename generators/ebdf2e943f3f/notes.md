# Working notes: ebdf2e943f3f

## Repair outcome (version 3.2.0)

The selected Racket authority remains unchanged at `RULE_HASH = 59a5d1f77f1b`.
The repair changes only the generated curriculum and its executable semantic
contract.

### Defect

All three canonical pairs contain isolated three-cell monochrome L-components.
Consequently, the plausible rival **complete only isolated size-three L
components** fits 3/3 canonical pairs even though the intended rule scans every
qualifying local 2x2 window.  The version-3.0.0 sampler also emitted only
isolated windows, so its generated lessons never refuted that rival.

Prior return `local-random-af2b51f06e3b` was used only as a lead.  Its retained
notes correctly emphasized all-window completion, corner coverage, colour reuse,
exact axes, and unchanged authority, but they did not test object connectivity.
All measurements in this return were repeated against the pinned assignment
baseline.

### Selected distribution

Two residues in each four-sample cycle (`sample_index % 4 in {1, 2}`) now place
two non-overlapping 2x2 windows edge-to-edge and give them the same colour.  The
painted cells become one larger 4-connected component, while each local window
still has exactly three equal non-zero cells and one zero.  The Racket rule fills
both holes; the isolated-component rival fills neither connected-window hole.
Horizontal and vertical connected layouts alternate across cycles.

A lesson has four demonstrations and one query.  The production sampler uses
five consecutive sample indices.  Because every four-index period has two
connected witnesses, every possible held-out query leaves at least one witness
among the four demonstrations.  The corner-orientation schedule was also made
rotation-safe: any three of the four schedule residues cover all four missing
corners, so every five-pair bundle remains identifiable after any one query
rotation.

Connected odd residues keep unrelated windows colour-distinct; connected even
residues reuse one colour for all windows.  Isolated residues retain the
canonical-profile anchor and independent-colour branch.  Exact caller controls
remain only `grid_h`, `grid_w`, and `n_blocks`.

### Executable contract and reusable probe

`isolated_l_components_only` is declared in `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.  The
`connected_same_colour_windows` witness is bound to that rival through
`WITNESS_RIVALS`.  The six corner/colour predicates are explicitly classified
as `BRANCH_WITNESSES`, not rival claims.  `lesson_identifiable` now requires a
connected same-colour counterexample in addition to all four corners, multiple
corner types in one scene, and both reused/distinct colour branches.

`workspace/shortcut_probe.py` discovers the generator's declarations rather
than copying rival names.  It verifies canonical fit, generated
counterexamples, every requested cyclic start, and every held-out query.

### Final evidence

Final generator SHA-256:
`e83848a12fe250faf2caa2088b2c77e6a8d1d2e75f6813114b3b373f99610398`.

- Full after battery: 12/12 green (`checks/after-final/`).
- Required semantic rotations: 12/12 lessons and 60/60 rotations identifiable.
- Task-test portable snapshot: 92/92 executions passed (46 logical tests loaded
  in both source and staged layouts).
- Racket lesson census: 300/300 lessons, 1,500 pairs, 1,500 rotations,
  0 ambiguities, 0 hook warnings, 0 scoring errors; 1,485 unique inputs.
- Task-local exhaustive probe: 512 bundles, 2,560 pairs, 2,560 rotations,
  minimum two connected witnesses per bundle, zero failures.
- Exact Racket-verified counterexample: `checks/shortcut-witness/`.

### Limits retained deliberately

This is finite evidence against a declared rival, not a proof of unique
induction.  The generator still does not emit qualifying windows that share
painted cells, unrelated decoys, or every possible connected topology.  Its new
connected family is limited to one edge-adjacent same-colour pair, with any
remaining windows isolated.  Those restrictions should be broadened only with
additional task-linked evidence and a new minimized regression case.

Imported associated notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e83848a12fe250faf2caa2088b2c77e6a8d1d2e75f6813114b3b373f99610398`.

# DECISIONS — `ebdf2e943f3f`

## D1 — Treat the isolated-component interpretation as the strongest rival

**Choice.** Define `isolated_l_components_only`: identify the same qualifying
2×2 windows, but fill a missing corner only when the painted cells belong to a
4-connected monochrome component of size exactly three.

**Original rationale.** The canonical inputs show only isolated three-cell Ls,
so this object-level rule fits all 3/3 canonical pairs. The prior return
`local-random-af2b51f06e3b` tested fixed-corner, first-match, colour, and
complete-only-one-window ideas, but its retained notes did not test component
connectivity. That return was a lead, not accepted evidence.

**Alternatives considered.** Fixed corner, first qualifying window only,
one-colour-per-window, one shared colour per scene, and identity/geometric
transforms were weaker: the baseline schedule already exposed multiple corners,
multiple windows, reused and distinct colours, and non-identity outputs.

**Probe.** The rival was required to fit every canonical pair before use. It
fits 3/3 under `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and
`SEMANTIC_RIVALS` in `checks/lesson-census.json`. The exact disagreement is in
`checks/shortcut-witness/`.

**Failure modes.** This rival is only one finite hypothesis. Passing it does not
prove unique induction or cover other object/window decompositions.

## D2 — Add edge-connected same-colour windows without broadening the rule

**Choice.** On residues 1 and 2 of each four-sample cycle, place two
non-overlapping 2×2 windows exactly two columns apart or two rows apart, and
assign the same colour to both. Their painted cells touch cardinally, producing
one larger component while preserving two independently qualifying local
windows. Alternate horizontal and vertical layouts across cycles.

**Original rationale.** A counterexample had to be lawful under the existing
strict scene grammar, leave the Racket rule unchanged, and isolate connectivity
as the distinguishing feature. Edge-connected non-overlapping windows satisfy
all three conditions.

**Alternatives considered.** Overlapping qualifying windows were rejected
because the canonical evidence does not establish shared painted cells and the
strict grammar deliberately forbids them. Unrelated decoy objects were rejected
for the same reason. Merely reusing a colour at a distance was already present
and does not refute the component-size shortcut.

**Probes.** `connected_same_colour_windows` fires only when the intended mirror
and rival disagree. The final semantic sample observed 291/600 firings across
all bands; the witness claim held 60/60 sampled checks. The Racket witness at
seed 1000, sample 1 differs at exactly two cells.

**Failure modes and limits.** The new family covers one edge-adjacent pair, not
all connected topologies. Remaining windows are isolated. Painted cells never
overlap. The adjacency cadence is deterministic and discoverable.

## D3 — Make the five-pair lesson rotation-safe

**Choice.** Keep `EXAMPLES_NEEDED = 4`; assemble four demonstrations and one
query from five consecutive samples. Put connected witnesses on two adjacent
residues in every four-index period, so holding out any one pair leaves at least
one rival-refuting demonstration.

**Original rationale.** A witness frequency near 50% does not guarantee that a
complete lesson contains a witness, and an ordered-production pass does not
establish arbitrary query rotation. Two witnesses per period provide a simple,
checkable combinatorial guarantee for this five-pair assembly.

**Alternatives considered.** One witness per four samples fails when that pair
is the query. Random witness placement would require rejection/resampling and
would be harder to replay. Increasing the demonstration count was unnecessary
once the schedule could be repaired at four.

**Probes.** The task-local probe covers starts 0–15, seeds 1000–1007, four bands,
and every held-out position: 512 bundles, 2,560 rotations, no failures, minimum
two witnesses per bundle. The source-bound Racket census separately checks 300
production lessons and 1,500 rotations.

**Failure modes.** The downstream assembler must preserve the declared
five-consecutive-pair policy. A different shuffler or sparse index selection
needs its own identifiability check.

## D4 — Repair corner coverage at the lesson level, not just per draw

**Choice.** Use complementary missing-corner patterns across the four schedule
residues so any three residues still cover corner indices `{0,1,2,3}`. Connected
layouts use adjacency-compatible corner pairs; isolated residues begin at
complementary bases.

**Original rationale.** The first rotation-focused regression exposed that some
four-demonstration sets lost a corner orientation after one pair became the
query. Correct labels per grid were insufficient; the lesson itself needed to
teach orientation independence.

**Alternatives considered.** Requiring every individual scene to contain all
four corners would exclude lawful two- and three-window controls. Dropping the
all-corners lesson contract would permit a fixed-orientation shortcut.

**Probes.** TDD retained the failing rotation schedule and final green run under
`checks/tdd-red-rotation-schedule/` and
`checks/tdd-green-rotation-schedule/`. Final required semantic evidence reports
60/60 identifiable rotations.

**Failure modes.** This guarantees coverage for the actual cyclic assembly, not
for arbitrary subsampling of fewer than four demonstrations.

## D5 — Declare semantic roles explicitly

**Choice.** Put the rival in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and
`LESSON_COMPETITORS`; bind the connected witness through `WITNESS_RIVALS`; put
corner and colour predicates in `BRANCH_WITNESSES`; require a connected
counterexample in `lesson_identifiable`.

**Original rationale.** The baseline semantic gate passed with six weak
witnesses and no task-specific rival. An intermediate run then treated all
unclassified witnesses as weak claims. Explicit role declarations make the
contract machine-checkable and prevent branch coverage from masquerading as a
rival assertion.

**Alternatives considered.** Leaving the rival only in prose would not protect
future schedules. Binding every witness to the rival would be false: corner and
colour witnesses cover branches but do not necessarily distinguish the
isolated-component rule.

**Probes.** Final semantic evidence has zero weak witnesses, six branch
witnesses, one rival-bound witness, and a 60/60 valid rival claim.

**Failure modes.** The declarations are executable Python and must remain pure,
deterministic, and source-bound. Adding a new rival requires a canonical-fit
check and an emitted counterexample.

## D6 — Preserve authority and exact controls

**Choice.** Leave the Racket rule, canonical ledger, dimensions, block-count
axes, and strict grammar unchanged. Bump only generator version `3.0.0` →
`3.2.0`.

**Original rationale.** Racket already expresses the intended local scan and
matches all canonical outputs. The previous review had already reduced caller
controls to observable `grid_h`, `grid_w`, and `n_blocks`; the current defect
was curriculum coverage, not authority or override semantics.

**Alternatives considered.** Editing Racket to recognize connected components
would encode the shortcut rather than fix it. Adding a `connected` override was
rejected as unnecessary API surface; the schedule provides coverage without a
new caller contract.

**Probes.** Authority sync and rule smoke are green; the rule hash remains
`59a5d1f77f1b`. The final override matrix accepted 18,000/18,000 draws with no
findings, and the profile floor hit every band.

**Failure modes.** The generator remains catalog-unapproved and only
provisionally safe; this review does not change approval or training admission.

## D7 — Build a reusable declaration-driven shortcut probe

**Choice.** Add `workspace/shortcut_probe.py`, which discovers actual
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and
`WITNESS_RIVALS` rather than copying names into the tool.

**Original rationale.** Future agents need a fast way to check canonical fit,
exact generated disagreements, cyclic lesson starts, and query rotations before
running the longer Racket census.

**Alternatives considered.** A one-off notebook or hard-coded rival list would
drift silently. Using only `rule_mirror` as final authority was rejected; the
probe labels itself diagnostic and is paired with Racket apply/battery/census
evidence.

**Probes.** The source and portable staged-runtime tests both import and run the
tool. Its final report covers 512 bundles and 2,560 rotations with zero failures.

**Failure modes.** It tests direct deterministic draws, finite declarations,
and Python-mirror labels. Runner rejection/resampling and Racket authority are
covered separately by the public checks.
