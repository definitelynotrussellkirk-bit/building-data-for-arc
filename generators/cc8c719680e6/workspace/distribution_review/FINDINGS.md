# Distribution review: cc8c719680e6

Reviewed source SHA-256: `fcb5e074619f09fc2cdbac112de79105426765a444efe592284d15f071d52a78`.
Canonical executed rule: `8f9e53b42241`.
The exact reviewed generator is preserved in `baseline_generator.py`. No selected
generator, canonical rule, shared source, or selected test was edited by this review.

## Primary finding: finite lessons rarely teach the connectivity distinctions

Two plausible rivals fit all three canonical train/test pairs:

1. Frame each same-color **8-connected** component.
2. Frame each **color-blind 4-connected** foreground component, using the color
   of its first source cell.

The baseline can refute both rivals, but its randomized anchors supply their
counterexamples only incidentally. They are absent from `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and the existing witness declarations. Consequently the
current lesson check can report success for a consecutive generated lesson even
when one of these rivals fits every demonstration and fails its query.

An initial source-only hypothesis that contact was impossible was rejected.
Despite `_anchors` describing a separating row/column, its primary bounding box
can end at a split and another box can begin at split + 1. Contacts have nonzero
support. The defect is inadequate coverage within a finite lesson.

### Independent baseline census

For each difficulty, 1,000 generator-level four-demo windows were drawn with
seed `810000 + 10000 * band_index + repetition` and consecutive indices
`4 * repetition` through `4 * repetition + 3`. All 12,000 inputs passed the
baseline `self_check`. These are direct `generate` windows, not a claim about a
separate production lesson materializer.

| Difficulty | Four-demo windows | 8-connected rival survives every demo | Color-blind rival survives every demo |
|---|---:|---:|---:|
| easy | 1,000 | 994 | 821 |
| medium | 1,000 | 991 | 794 |
| hard | 1,000 | 998 | 819 |
| Total | 3,000 | 2,983 (99.43%) | 2,434 (81.13%) |

Only 17 of 12,000 individual inputs refuted the 8-connected rival. Only 592
refuted the color-blind rival. A separate single-draw check of all 144 exact-axis
Cartesian combinations found four and eighteen discriminators respectively.
The override results establish sampled constructibility, not a guarantee that
every override draw teaches either distinction.

Counts were computed by independently implemented object extraction, morphology,
and outline functions in `probe.py`; no producer semantic helper supplied them.
The 55-input retained reference batch includes canonical inputs, 48 ordinary
generated inputs, the first naturally occurring discriminator for each rival,
and two authored contact cases. The independent outline matched all 55 real
Racket outputs. Source identities, exact inputs, and authoritative labels are in
`racket.json`; the census retains seeds and scope in `census.json`.

### Exact consecutive lessons with real Racket labels

| Rival | Difficulty | Seed | Demo indices | Query index | Existing lesson-hook errors |
|---|---|---:|---|---:|---|
| Color-blind 4-connected components | easy | 810004 | 15, 16, 17, 18 | 19 | `[]` |
| Same-color 8-connected components | easy | 810078 | 311, 312, 313, 314 | 315 | `[]` |

For both rows the rival matches all four Racket demonstration outputs and
disagrees with the Racket query output. All ten source grids are retained in
`lesson_inputs.json`, all executed labels and rule hashes in `lesson_racket.json`,
and the comparisons using those labels in `reference_verification.json`.
`lesson_meta.json` contains the replay metadata.

### Small lawful witnesses

The authored 9x13 case has four distinct high colors and touching geometry.
A 3x3 plus and a neighboring 2x2 L have orthogonally adjacent source cells of
different colors. The baseline accepts the input, and the color-blind rival
differs from its reference output at seven cells.

The authored 13x9 case has three interior components using low colors and exactly
one repeated pair. A 3x3 staircase and a 2x2 L of the same color touch only
diagonally. Their bounding-box footprints remain disjoint and their 4-connected
components remain separate. The baseline accepts the input, and the 8-connected
rival differs from its reference output at twelve cells. These cases are the
last two inputs in `inputs.json` and `racket.json`.

## Highest-payoff bounded repair

Guarantee an orthogonal, different-color contact in generalized schedule slot 1
and a diagonal-only, same-color contact in generalized schedule slot 3. Construct
the contact pairs directly, keep their bounding-box footprints disjoint, and
randomize lawful orientations and translations. Preserve the existing canonical
slots and the observable axis contract. Add the two executable rivals and exact
contact witnesses to the task's semantic contracts, then require every sliding
four-demo window to refute both.

This targets the demonstrated lesson failure without broadening the rule, adding
overlap ambiguities, or changing the canonical Racket solution. Exact override
combinations should remain constructible. Explicit separated layouts can remain
available as additional diversity without replacing the guaranteed default
counterexamples.

## Secondary support limitation

The canonical inputs have three distinct joint morphology profiles. The baseline
generates exactly four joint morphology profiles across the 12,000-input census:
canonical train pair 0, canonical test pair 0, and the fixed generalized 3- and
4-component profiles. Canonical train pair 1's joint profile is never generated:

`((4, 2, 3, 2, 0), (5, 2, 3, 1, 0))`

Here each tuple is `(cell_count, min_bbox_span, max_bbox_span, missing_bbox_area,
interior_source_cell_count)`. That missing profile is accepted by the strict
predicate but `_canonical_profile_layout("canonical_9", ...)` always chooses the
held-out canonical morphology. The baseline still meets its stated 40% strict
floor because 50% of natural returns use the other two canonical profiles.
This is a support limitation, not a canonical-label mismatch. Sampling both
9x9 canonical morphology variants would be a small optional improvement; the
connectivity lesson repair is the higher priority.

Generalized components also remain limited to a size-five 3x3 primary shape and
2x2 L shapes. Larger or denser irregular components would expand geometry support,
but are not required to repair the concrete finite-lesson defect demonstrated
here.

## Reproduction

Run from the extracted packet root. Reference output paths must be new on replay.

```bash
python3 run_with_racket.py python3 generators/cc8c719680e6/workspace/distribution_review/probe.py
python3 run_with_racket.py python3 -m arcpuzzles apply cc8c719680e6 --input generators/cc8c719680e6/workspace/distribution_review/inputs.json --out generators/cc8c719680e6/workspace/distribution_review/racket.json
python3 run_with_racket.py python3 generators/cc8c719680e6/workspace/distribution_review/probe.py --prepare-lessons
python3 run_with_racket.py python3 -m arcpuzzles apply cc8c719680e6 --input generators/cc8c719680e6/workspace/distribution_review/lesson_inputs.json --out generators/cc8c719680e6/workspace/distribution_review/lesson_racket.json
python3 run_with_racket.py python3 generators/cc8c719680e6/workspace/distribution_review/probe.py --verify-reference
```

The probe imports the retained baseline regardless of later selected-generator
changes. A later `apply` receipt may name the then-current selected generator;
the input-generation identity remains the baseline hash in the census. The
executed canonical rule identity must remain explicit in either case.
