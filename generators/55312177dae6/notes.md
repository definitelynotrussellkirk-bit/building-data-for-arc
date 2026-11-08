# Working notes: 55312177dae6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `7daf814989a30ae3630996f2b91cacb815844062c8ab9b8a4096787e9bf6e61f`.

# Decisions — 55312177dae6

## D1. Keep the canonical authority unchanged

**Choice.** Preserve the Racket rule and pin its normalized hash
`39919c9ecf3d` in the generator.

**Reason.** The canonical examples, written solution, and program agree: among
blue components, select the one rotational class that occurs at least twice and
emit its lexicographically canonical rotation in cyan. The pre-repair defects
were in sampling, validation, metadata, and curriculum—not the authority.

**Probe.** Canonical replay accepts and mirrors all three usable pairs; final rule
smoke reports zero mirror mismatches over 120 generated inputs.

**Rejected alternative.** Weakening the Racket program to tolerate no-match grids
would legitimize generator errors and make the task ambiguous. Instead, no-match
inputs are rejected before rule execution.

## D2. Advertise only pixel-observable controls

**Choice.** Replace the prior metadata surface with five axes:
`grid_h`, `grid_w`, `n_distractors`, `target_area`, and `match_rotation`.

**Reason.** The old `family`, palette, density, texture, singleton color-count,
and position labels were ignored, aliases, or non-choices. They produced 39,315
override findings and trained callers to distrust the metadata.

**Implementation.** All five values pass through keyed `GenCtx` draws—even
scheduled defaults use singleton keyed draws—then `observe_overrides` recovers
those values from the pixels. Unknown controls, booleans, floats, strings, and
out-of-range integers fail loudly.

**Rejected alternative.** Keeping compatibility aliases and declaring them
“diagnostic” would preserve a misleading public surface without adding any
instance diversity.

## D3. Use a finite, complete target-shape domain

**Choice.** Enumerate connected fixed polyominoes of area 2..5 with at most a
4x4 bounding box. Targets are area 3..5 classes with four distinct rotations;
distractors may include area 2 to retain canonical support.

**Reason.** Four distinct target orientations make `match_rotation=1..3` exactly
observable. This domain has 18 target outputs and includes every such free
polyomino class, so `EXPECTED_OUTPUT_CODOMAIN = 18` is a truthful finite-codomain
declaration rather than a waiver.

**Failed iteration.** A first implementation restricted shapes to a 3x3 box. All
36 tests passed, but lint measured only 12 distinct outputs (8%). Expanding to
4x4 reached all 18 outputs. Lint still warned on the ratio, so the finite codomain
was explicitly declared; the final lint then passed. Intermediate logs are under
`checks/lint/`, `checks/lint-r2/`, and `checks/lint-r3/`.

**Limit.** Straight and rotationally symmetric target classes are excluded because
some requested quarter-turn offsets would be pixel-indistinguishable. This is an
explicit grammar decision, not an accidental sampler gap.

## D4. Construct scenes exactly; never return a retry residue

**Choice.** Use exhaustive orientation enumeration and deterministic
backtracking with 8-neighbor clearance.

**Reason.** v3.0.1 had nested retry caps followed by `return g`; the final `g`
could lack a match or distractor. Exact search is small for three or four
area-2..5 objects on the declared grids and eliminates that failure class.

**Rejected alternatives.** A fixed four-corner 3x3-slot layout was simpler but
restricted output shapes and made positions too regular. Unbounded random retry
would hide impossibility and hurt replayability. Exact search gives deterministic
success or an explicit exception.

## D5. Make the validator describe the authority's true preconditions

**Choice.** Validate ARC type/range, rectangle shape, colors 0/1, three or four
4-connected components, 8-connect separation, object area bounds, exactly one
rotation class of count two, singleton distractor classes, at least one
distractor, and different target orientations.

**Reason.** The Racket authority calls `first` on the repeated-class search; a
no-match grid is not a lawful edge case. Blank, singleton, short-line, solid block,
all-same, and no-distractor scenes are therefore negative fixtures, not textures.

**Probe.** The red tests demonstrate v3.0.1 accepting these cases. Final defect
lint reports zero findings, and canonical examples remain accepted 3/3.

## D6. Schedule counterexamples, not merely random diversity

**Choice.** Cycle four profiles:

1. `reflection_and_order` — a reflected distractor refutes dihedral grouping and
   a distractor appears before both targets;
2. `target_largest` — refutes smallest-object selection;
3. `target_smallest` — refutes largest-object selection;
4. `area_frequency_tie` — refutes the modal-area shortcut that fits all canonical
   examples.

All scenes use differently oriented target copies, refuting exact-orientation
matching.

**Reason.** The canonical set alone admits at least `first_component` and
`modal_area`. Random witness frequency is insufficient if a four-demo lesson can
miss a needed branch, so `lesson_identifiable` checks whole windows against the
actual declared rival functions.

**Probe.** The battery verifies six witnesses and 12/12 smoke lessons. The larger
probe verifies 128/128 lessons per band, all four cyclic starts equally, with all
six rivals separated in every lesson.

## D7. Deliberately refute “first object,” then test for replacement shortcuts

**Choice.** Place one distractor first in row-major order on every generated grid.
Allow the two targets to occupy any two of the remaining three component indices.

**Reason.** “Select the first component and canonicalize it” fits every canonical
pair, so every generated lesson should directly falsify it.

**Risk and probe.** A rigid replacement shortcut such as “select the second” or
“select the last” would be equally harmful. The source-bound position probe scans
2,000 draws per band and observes all target-index pairs `(1,2)`, `(1,3)`, and
`(2,3)` in every band (`checks/position-probe/report.json`).

## D8. Use four demonstrations per generated lesson

**Choice.** Set `EXAMPLES_NEEDED = 4`, matching the profile cycle.

**Reason.** Any cyclic window of four contains one example from each profile.
This makes curriculum sufficiency deterministic rather than probabilistic.

**Rejected alternative.** Three demonstrations could work for some seed/profile
combinations but cannot guarantee all four scheduled distinction branches.

## D9. Keep independent probes independent

**Choice.** Add `workspace/reference_probe.py`, `workspace/lesson_probe.py`, and
`workspace/position_probe.py`.

**Reason.** Tests should not prove a generator with its own implementation
helpers. `reference_probe.py` independently implements component extraction,
rotation canonicalization, authority output, canonical loading, and observable
axis decoding. The other tools import the exact source path, hash it, and iterate
the generator's live rival declarations rather than copying a rival-name list.

**Limit.** These are finite deterministic censuses of the declared sampler. They
do not establish universal identifiability or predict Qwen3.5-9B accuracy.

## D10. Preserve genuine failures and execution interruptions

The initial test-first run (34 failed, 2 passed) is retained at
`checks/55312177dae6_tdd_red.log`. Two synchronous full-battery invocations were
interrupted by the execution envelope while their subprocesses were active;
their partial checkpoint directories are retained as `checks/after/` and
`checks/after-r2/`. A detached fresh run under `checks/after-r3/` completed all 12
stages green. These interruptions are not represented as source failures.
