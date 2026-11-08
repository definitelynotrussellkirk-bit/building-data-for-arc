# Working notes: f7b828a70061

## Current intended rule

The isolated control cell at `(0,0)` is one of `2,3,4,5`. After clearing it,
find nonzero color-insensitive 4-connected components, choose the unique largest
by cell count (ties would be top-left), crop that component's bounding box while
preserving its colors and internal zeros, and rotate the crop: `2` identity,
`3` clockwise, `4` 180°, `5` counter-clockwise. The authoritative Racket rule
was not changed. Its pinned `RULE_HASH` is `d95bdc7a1a1a`.

## Review history and reversal

No prior return was used as a repair lead; `evidence/associated_notes.jsonl` was
empty. The lead was the selected baseline generator plus the retained before
checks. Baseline version `2.1.0` (SHA-256
`55d6ac1d532fb13b25d901afd200bf45c709583ed8ea2746a5a3d02c4994e6c9`)
advertised broad 10–26-cell grids, 5–20-cell main objects, up to nine body
colors, multiple random distractors, and degenerate textures. The focused before
defect lint showed that this distribution was far outside the five canonical
profiles, advertised controls were not honored, validation accepted weak
impostors, `RULE_HASH` and semantic contracts were missing, and the sampler did
not teach a concrete canonical-fitting rival.

Version `3.1.0` reverses that breadth-first choice. It deliberately uses a
narrow source-shaped curriculum with exact observable controls and a guaranteed
counterexample to the strongest tested shortcut. Final generator SHA-256:
`eea80f00b8851ea76a5a9952f98ea2828a1c979ac2ba4a57e9e4202f0ec722b5`.

## Distribution decisions

- Cycle the five canonical `(height, width, body-palette-size)` profiles:
  `(7,9,2)`, `(8,10,2)`, `(7,10,1)`, `(8,9,1)`, `(9,11,2)`.
- Cycle commands `2,3,4,5`; use seven demonstrations plus one query so any
  leave-one-out query rotation still leaves all four command meanings visible.
- Generate one sparse connected 3×3 main object of 6–8 cells (`frame` or
  `stair`) and one external 5-cell connected decoy that also spans 3×3.
- Put the decoy first in reading order. Cell count therefore selects the main,
  while largest-bounding-box-area with top-left tie-breaking selects the decoy.
- Reserve the command color for `(0,0)` and use exactly one or two body colors,
  forcing every selected body color to appear in the main object.
- Advertise only controls that are exact and recoverable from pixels:
  `grid_h`, `grid_w`, `command`, `main_size`, `main_shape`, `palette_size`.

## Strongest tested shortcut

The five canonical demonstrations are all fit by: “after clearing the command,
select the component with largest bounding-box area, tie by top-left; crop and
rotate it.” The exact retained counterexample is
`counterexamples/largest-bbox-area-shortcut.json`. Both components span 3×3;
the earlier decoy has five cells and the later main has eight, so the rival
selects the decoy while the authority selects the main. The production sampler
constructs this disagreement on every draw.

The earlier candidate “crop all nonzero cells” was rejected as the strongest
rival because canonical demonstrations already contain external distractors and
therefore refute it. Other finite rivals may remain; the declarations and census
cover the explicit largest-bbox-area competitor, not all possible programs.

## Validation and teaching contract

`self_check` accepts the five canonical inputs and the generated source-shaped
domain: 7–9 by 9–11, isolated legal command, one unique sparse largest component
of size 3–8, at most one smaller component outside its bounding box, and one or
two body colors excluding the command. Production generation is narrower
(main size 6–8, exactly one 5-cell decoy). `observe_overrides` recovers every
advertised axis. `lesson_identifiable` requires all four commands and at least
one explicit bounding-box-area tie witness. The declared witness/rival is also
registered as the canonical shortcut and lesson competitor.

## Evidence and current status

- Full after battery: 12/12 stages green in `checks/after/`.
- Portable selected-task tests: 49/49 passed in `checks/task-tests-final/`.
- Profile floor: 60/60 exact canonical-profile hits and 60/60 envelope hits.
- Semantic smoke: 600/600 strict draws, witness fired 600/600, rival claims
  verified 60/60, and 0/96 ambiguous query rotations.
- Large source-bound census: 300/300 lessons, 2,400 production pairs and 2,400
  rotations, zero ambiguity, 2,337 unique inputs in
  `checks/lesson-census.summary.json`.
- Independent compact reproducer: `workspace/qualify.py` and
  `checks/qualification.json`.

## Known limits and open findings

The generated manifold is intentionally narrow: two objects, fixed 3×3 object
bounding boxes, two shape families, one or two body colors, and canonical grid
profiles. This is a curriculum decision, not a claim that the authority applies
only there. The finite census checks one declared rival and does not prove
universal identifiability. A future expansion should preserve exact canonical
profile support and retain explicit witnesses against any newly plausible
selection shortcut rather than restoring unconstrained random breadth.
## Current reviewer considerations

Source SHA-256: `eea80f00b8851ea76a5a9952f98ea2828a1c979ac2ba4a57e9e4202f0ec722b5`.

# Decisions for f7b828a70061

## 1. Replace broad random generation with a source-shaped curriculum

**Prior choice.** Version `2.1.0` sampled much larger grids, large arbitrary
polyomino/rectangle/line objects, up to nine body colors, multiple distractors,
and degenerate textures.

**Decision.** Cycle the five canonical height/width/body-palette profiles
exactly, keep the command isolated at `(0,0)`, and generate one main component
plus one external decoy.

**Reason.** The before defect lint found structural and scalar distance from the
canonical source, ignored controls, and weak validation. The final profile stage
measured 60/60 exact profile hits and 60/60 envelope hits. This is preferable to
claiming diversity that does not resemble the task source.

**Rejected alternative.** Merely reduce the old ranges. That would still leave
random object counts, unobservable controls, and no guaranteed semantic witness.

**Limitation.** The new manifold is intentionally narrower than the authority's
full legal domain.

## 2. Teach cell-count selection with an equal-bounding-box-area decoy

**Decision.** The main contains 6–8 cells in a sparse 3×3 box. The decoy contains
five cells in another 3×3 box and is earlier in reading order.

**Reason.** “Select largest bounding-box area, tie top-left” fits all five
canonical demonstrations. Equal box areas make the rival select the earlier
five-cell decoy, while the intended cell-count rule selects the larger main.
This is a stronger teaching witness than merely including a small distractor.

**Exact probe.** `counterexamples/largest-bbox-area-shortcut.json` has an
8-cell main and a 5-cell decoy, both area 9. The authority and rival outputs were
compared in focused tests, the strict semantic gate, the independent
qualification helper, and the source-bound census.

**Rejected rival candidate.** “Crop the bounding box of all nonzero cells” is
already contradicted by canonical examples containing external distractors, so
it is not the strongest canonical-fitting shortcut.

**Failure mode guarded.** If either object loses its 3×3 span, or if the decoy
ceases to be earlier, the witness contract and focused tests fail.

## 3. Use two symmetry-distinguishable sparse main shape families

**Decision.** Main shapes are `frame` and `stair`, each defined for sizes 6–8
and randomly transformed by dihedral symmetries. The decoy uses its own connected
five-cell shape and symmetry.

**Reason.** Two families preserve shape variation while keeping override
observation exact and every object within the canonical-scale 3×3 envelope.
Sparse boxes ensure the crop preserves meaningful internal zeros.

**Rejected alternative.** Restore arbitrary random polyominoes immediately.
That would complicate exact shape observation and make witness guarantees less
transparent. Such an expansion can be added later with new tests and rival
coverage.

## 4. Reserve the command color and bind body palette size to one or two

**Decision.** Draw one or two body colors from ARC colors excluding the command,
and force every chosen color to appear in the main object.

**Reason.** The five canonical profiles contain one or two body colors. Excluding
the command prevents it from joining the body semantically, and forcing color
visibility makes `palette_size` observable rather than merely requested.

**Rejected alternative.** Keep the old one-to-nine-color axis. It was far from
canonical and could advertise colors not visible in the selected object.

## 5. Advertise only exact observable controls

**Decision.** Keep six axes: `grid_h`, `grid_w`, `command`, `main_size`,
`main_shape`, and `palette_size`. Validate literal types and domains before
calling the generator context, and recover all six with `observe_overrides`.

**Reason.** The old `position_bias` and `texture` controls were aliases or dead
paths, and several numeric controls were ignored by generation. The final
override stage accepted 12,510/12,510 draws over 139 cases with zero findings.

**Rejected alternative.** Preserve deprecated axes for compatibility. There was
no demonstrated consumer contract worth retaining, and silent controls are more
dangerous than a smaller honest API.

## 6. Seven demonstrations, cyclic commands, and required query rotations

**Decision.** Set `EXAMPLES_NEEDED=7`; commands cycle `2,3,4,5`. A lesson has
seven demonstrations and one query, covering two complete command cycles.
`lesson_identifiable` requires all four commands and a bbox-area witness.

**Reason.** Holding out any of the eight pairs leaves all four command meanings
among the remaining seven. This makes the lesson robust to the assembly system's
leave-one-out rotations rather than only the default ordered query.

**Evidence.** The semantic smoke found 0/96 ambiguous rotations. The larger
census found 0/2,400 ambiguous production pairs and 0/2,400 ambiguous rotations
across 300 lessons.

**Rejected alternative.** Four demonstrations. A random four-pair lesson can
omit a command meaning, as independently reproduced in audit target
`018e2800eef6`.

## 7. Keep the Racket authority unchanged

**Decision.** Pin `RULE_HASH=d95bdc7a1a1a` and change only the selected
Python generator, tests, notes, counterexample, and qualification helper.

**Reason.** Canonical outputs and the Racket rule already express the intended
cell-count/crop/rotation transformation. The defect was sampling and teaching,
not authority semantics. Authority synchronization, rule smoke, and Racket lint
all passed in the final battery.

## 8. Add a compact independent qualification tool

**Decision.** Add `workspace/qualify.py` with a focused test.

**Reason.** Future agents can reproduce the decisive acceptance facts without
rerunning the entire twelve-stage battery: canonical rival fit, generated
witness/disagreement, strict acceptance, deterministic replay, profile counts,
and a joint exact-control probe.

**Limitation.** It is an independent smoke/qualification report, not a substitute
for the official battery or source-bound lesson census.
