# Working notes: 56169a1e5c1d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `210a69156edcd6bd0ee6e6b04d6313e67535474c7ea71a71aadd11117f8383d2`.

# Decisions: 56169a1e5c1d

## Evidence lead and baseline treatment

I used prior return `review_response_94e629245588_x` only as a lead.  Its retained
notes correctly highlighted the need for scheduled adversarial controls and
canonical morphology anchors, but all current claims were remeasured against the
pinned packet baseline.  The baseline 12-stage battery was green; the defect was
found only by the required source-bound `lesson-census --rotate-query` run.

## D1 — Preserve the intended rule and Racket authority

**Choice.** Keep the canonical transformation unchanged: fill a midpoint only for
equal nonzero endpoints at displacement `(2, ±2)` when the midpoint is blank.
Keep `RULE_HASH=d1b9f133bb98` and make no canonical/Racket edit.

**Rationale.** Canonical execution, the Python mirror, rule smoke, and selected
authority already agreed.  The failure was in lesson composition, not labels or
rule semantics.

**Alternatives rejected.** Weakening the competitor set, narrowing the validator,
or changing labels would hide the teaching defect rather than repair it.

**Probe.** Before and after `rule_smoke`, `racket_lint`, and `authority_sync` are
green; the authority-set SHA-256 remains
`94f4c6a817a45628113d43cf48dd35a77f046f2ee3f945386a16caeb28d815a4`.

## D2 — Use overlapping witness bundles

**Choice.** Replace the single-family cycle with three overlapping bundles:

- axis-aligned + wrong-distance/different-color;
- wrong-distance/different-color + blocked-midpoint;
- blocked-midpoint + axis-aligned.

The wrong-distance bundle includes both an equal-color distance-three diagonal
and a different-color distance-two diagonal, so it refutes two independent
extensions.

**Rationale.** A lesson has three demonstrations plus one query.  In a four-pair
window, a shortcut witness must occur at least twice to survive arbitrary
one-pair holdout.  The overlapping three-cycle is the smallest deterministic
change that gives every family multiplicity two without increasing
`EXAMPLES_NEEDED`.

**Alternatives rejected.** Increasing the number of demonstrations changes the
training interface; random resampling only makes ambiguity probabilistic; putting
all four decoy families in every sample increases crowding and placement risk;
keeping one witness per slot is provably fragile under rotation.

**Failure retained.** `checks/task-tests-red/result.json` captures the new test
failing on the old schedule.  `checks/lesson-census-before.json.gz` records
553/1,200 ambiguous rotations.

## D3 — Keep canonical anchors at palette size five

**Choice.** Canonical-anchor samples use two active pair colors plus two decoy
colors and background, for palette size five.  The previous three-active-pair
anchor was reduced to two because the overlapping schedule needs two independent
decoy colors in every residue.

**Rationale.** This preserves exact 7x7/8x8/9x9 canonical morphology support while
leaving sufficient color budget for non-colliding controls.  Pair count is not
part of the transformation and remains explicitly controllable as 2 or 3.

**Alternatives rejected.** Reusing one decoy color for unrelated local roles can
create accidental active pairs or make the role ambiguous; adding a sixth palette
color would miss the strict canonical profile floor.

**Probe.** The profile-floor stage is green in every band, canonical samples are
accepted, and all exact override boundary combinations pass.

## D4 — Assign colors to avoid accidental fills

**Choice.** Active pairs retain distinct colors.  Axis and wrong-distance controls
use unused colors.  Mismatched endpoints reuse two active colors.  Blocked pairs
use an unused endpoint color and either an unused singleton blocker or one active
color, depending on residue.  Every tentative placement is accepted only if the
set of true fillable pairs remains exactly unchanged.

**Rationale.** This makes each decoy locally legible while `_try_decoy` provides a
semantic guard against unintended branch creation.

**Alternatives rejected.** Pure geometric spacing without recomputing active pairs
is brittle; random colors can accidentally create a new equal-color diagonal.

**Probe.** 18,000 exact-override draws had zero generation or grammar failures and
exactly the requested active-pair count (`checks/override-stress-final.json`).

## D5 — Add a rotation-complete regression

**Choice.** For every band and starts 0 through 8, generate four consecutive pairs
and hold each pair out in turn.  Require `lesson_identifiable` to return no
surviving competitor.

**Rationale.** The old test checked only the production query position and could
not detect the defect.  The new test directly encodes the downstream assembly
permission described in the assignment.

**Alternatives rejected.** Counting schedule modes is insufficient: frequency of
a witness does not prove it remains in the demonstrations after holdout.

**Limit.** The regression covers declared competitors and deterministic schedule
starts, not unknown rivals.  The 300-per-band-independent production census adds
1,200 rotations but remains finite.

## D6 — Preserve exact controls and broader scale

**Choice.** Keep `grid_h=7..16`, `grid_w=7..16`, and `pair_count=2..3` as the only
public axes.  Any exact override disables the periodic canonical anchor and is
honored literally.

**Rationale.** These values are recoverable from the emitted grid and useful for
boundary testing.  Colors, positions, and schedule residue are deterministic
nuisance variation, not advertised controls.

**Probe.** Staged override gate green; 18,000 direct stress draws cover every size
value 7..16, both pair counts, every band, and all three residues.

## D7 — Stop after semantic, mechanical, and human-solve convergence

**Choice.** Stop after the full battery, rotation census, focused tests, stress
probe, and post-repair visible solve all agreed.

**Rationale.** Further rule or architecture changes would be unrelated.  The
remaining uncertainty is the general induction limit shared by finite rival
sets, documented rather than overclaimed.

## D8 — Make the reusable stress probe work before assignment materialization

**Choice.** Discover the packet root from stable repository structure
(`repo/shared/runtime` plus the selected generator path), not from generated
`ASSIGNMENT.json`.

**Rationale.** The first exact-delta replay applied cleanly and its 14 task tests
passed, but the new helper then failed in the pristine packet because
`ASSIGNMENT.json` does not exist until `assignment.py` is run.  That was a defect
in the reusable tool, not in the generator.  The revised root predicate depends
only on files present in the original archive and remains specific enough to avoid
silently selecting an unrelated ancestor.

**Failure retained.** `checks/fresh-replay-tool-red-console.log` and
`checks/fresh-replay-tool-red.exit` preserve the initial failure.  The corrected
helper passed 1,800 draws from the pristine replay and 18,000 draws in the main
workspace (`checks/fresh-replay-override-stress.json` and
`checks/override-stress-final.json`).

**Fresh handoff probe.** The final source patch passed `git apply --check`, applied
to a new extraction, reproduced 14/14 focused tests, and produced the same
generator SHA-256 as the main checks and frozen solve source
(`checks/fresh-replay.json`).
