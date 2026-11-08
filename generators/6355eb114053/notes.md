# Center Completion — current generator decisions

## Rule and accepted domain

The selected Racket authority is unchanged, pinned at `d4bb39745d13`. A zero
interior cell is filled precisely when its four cardinal neighbors are the
same nonzero color. Existing colors and border cells remain unchanged. Labels
come from Racket. Python rivals are deliberately incorrect authoring probes.

`self_check` accepts rectangular integer-color grids of dimensions 3..30 with
at least one eligible center. Zero is the fixed background; booleans, floats,
ragged rows and colors outside 0..9 are rejected before neighborhood access.
Connected motifs, shared arms, and mixed valid/invalid neighborhoods are lawful.
No-change grids remain outside this sampler's positive-example domain, although
the Racket rule is defined on them. Separation is not a semantic requirement.

## Reversal of the v1.1.0 sampling choices

The old sampler placed only isolated true pluses at centers congruent to 1
modulo 3 and assigned colors 1,2,3 in placement order. Several advertised
controls had no effect; advertised size/count endpoints were rejected by
difficulty-specific bounds. Their original rationale is unknown.

Version 2.0.0 uses a guaranteed disjoint 3x3 packing followed by randomized
legal relocation. Positions and nonzero colors vary independently. Four actual
degrees of freedom are exposed: `grid_h`, `grid_w` (5..14), `n_pluses` (1..6),
and `palette_size` (1..9 nonzero colors). `n_distinct_colors` remains an exact
compatibility alias of `palette_size`, outside the independent `AXES` count;
conflicting values raise. `palette_kind`, `position_bias`, `density`, and
`texture` were ineffective or invalid controls and now raise an explicit
unknown/retired-axis error. Negative fixtures remain available only through
the private fixture helper for validator checks.

Dimensions are selected from feasible combinations before drawing the count.
The constructive capacity is floor(height/3)*floor(width/3). Requests exceeding
it fail with named incompatible axes; some such requests could fit shared-arm
pluses under the broader rule, but that layout family is not generated here.
Counts are measured from actual eligible centers and are never silently clipped.
Unused requested colors are added as singletons outside protected neighborhoods.

## Teaching distribution

Ordinary draws include a true positive plus and three near misses. Even sample
indices omit north on one neighborhood and mismatch south on another; odd
indices omit west and mismatch east. A third neighborhood has four matching
arms surrounding an already occupied, differently colored center. Ordinary
palettes have at least two colors. Colors are shared across roles and motif
locations are shuffled, avoiding a fixed color or slot as the role identifier.

`EXAMPLES_NEEDED=3` and the semantic schedule has period 2. A nominal four-pair
window contains two instances of each phase, so any single query holdout leaves
both phases in its three demonstrations. The executable contract checks nine
plausible rivals: the two opposite-direction pairs, each omitted cardinal
direction, majority-of-three, four-nonzero without equality, and overwriting an
occupied center. Actual production sampling, including accepted indices and
query rotations, is checked separately by the retained lesson census. Finite
rival coverage does not establish uniqueness among arbitrary programs.

Each band mixes broader dimensions/counts/palettes with anchors at the five
canonical dimension/palette profiles. This is fresh sampling, not canonical
grid replay. Hard broad draws favor larger positive counts; easy broad draws
favor one. All bands retain canonical support and the same semantic conditions.

## Current limitations and earlier audits

Small explicitly pinned canvases can lack room for all three decoys, and
`palette_size=1` cannot exhibit a color mismatch or differently occupied center.
Those controls remain exact; they carry no ordinary-lesson teaching guarantee.
The layout distribution is not uniform over packings. Touching positives and
border-only negative conditions are accepted/tested where appropriate but are
not separately scheduled production families. No cascade witness is claimed:
an eligible zero already has four nonzero neighbors, so filling it cannot
enable an adjacent zero under this particular rule.

The retained leads `review-0062d8f12011f0be:v0001` (override contracts) and
`review-15543a49112076fa:v0001` (north/south shortcut) both refer to the original
SHA `4af159e483bdcee1b4e8d74d70903356121d52671a01112df8b3904ecf822528`.
This repair addresses their reproduced mechanisms. Focused tests, the executable
rival contract, and the counterexamples document the resolution evidence.
The return requests explicit resolution of those two findings after integration;
changing source bytes alone does not clear their existing audit records.

## Verification entry points

Run the task tests through the public `arcpuzzles check 6355eb114053 --stage
task_tests --phase after` interface. `tests/test_center_completion.py` uses
portable canonical-data helpers, independent local-law observations, exact-axis
cases, malformed-grid cases, connected positives and four-pair rotations.
The return retains full before/after battery reports, a 100-lessons-per-band
Racket-labelled census with rotations, fixed-seed enumeration of both schedule
starts, source identities, and failure history. See its `RESULTS.json` for actual
commands and verdicts; these authoring checks do not admit trajectories to training.
## Current reviewer considerations

Source SHA-256: `e2eb16599edc6dcca97caebd13241d234f1876bfbeb2aadd8a620573104e8867`.

# Decisions — 6355eb114053, Center Completion

## Source and authority

The final generator is version 2.0.0, SHA-256 `e2eb16599edc6dcca97caebd13241d234f1876bfbeb2aadd8a620573104e8867`. The selected Racket rule remains unchanged at `d4bb39745d13`: fill a zero interior center exactly when its four cardinal neighbors share one nonzero color. Existing colors and border cells stay unchanged. Changing the rule to agree with a sampler shortcut was rejected because the error was in sampling and override contracts, not the canonical transformation. Source/rule identity and final checks are retained in [the final battery summary](checks/after-final/checks/6355eb114053_after_battery_summary.json), [the lesson census](checks/lesson-census.json), and [the schedule census](checks/schedule-census.json).

The old choices—centers on a fixed modulo-three lattice, colors assigned 1/2/3 in placement order, ineffective controls, and narrower difficulty-dependent override endpoints—have unknown original rationale. This report does not invent one. The retained leads `review-0062d8f12011f0be:v0001` and `review-15543a49112076fa:v0001` bind their mechanisms to old SHA `4af159e483bdcee1b4e8d74d70903356121d52671a01112df8b3904ecf822528`. Their reproduced override failures and north/south shortcut informed the repair. Integration should explicitly resolve those two findings using the new evidence; editing source alone does not clear their audit records.

## Four exact controls and one compatibility alias

The four independent axes are `grid_h` and `grid_w` (5..14), `n_pluses` (1..6 actual eligible centers), and `palette_size` (1..9 actual nonzero colors). Positions and colors vary independently. `n_distinct_colors` remains an exact compatibility alias for `palette_size`, outside `AXES`; contradictory simultaneous values raise an error. Removing that spelling entirely was rejected because preserving a useful existing caller spelling costs little. Counting both spellings as independent freedoms was rejected after it caused the intermediate lint and override failures retained in [the alias-collapse record](checks/intermediate/alias-collapse.json), [intermediate lint log](checks/after/checks/6355eb114053_after_lint.log), and [intermediate override log](checks/after/checks/6355eb114053_after_override.log).

The old `palette_kind`, `position_bias`, `density`, and public `texture` controls now raise explicit retired/unknown-axis errors. Accepting ignored arguments would preserve the original false contract; implementing several new distribution families would exceed this bounded repair. Negative textures remain private validator fixtures. Tests check both spellings, alias conflicts, unknown controls, single-axis endpoints, and joint realizations in [the task tests](repo/generators/6355eb114053/tests/test_center_completion.py). The final public task-test report records 62/62 passing tests in [checks/task-tests-final/result.json](checks/task-tests-final/result.json).

## Constructive placement and domain boundaries

The sampler first selects feasible dimensions, then counts, using capacity `floor(height/3) * floor(width/3)` for disjoint 3 × 3 neighborhoods. It begins from guaranteed packing and randomly relocates legal neighborhoods. This prevents unlucky retries from rejecting a valid declared packing request and removes the fixed lattice as a semantic cue. A completely unconstrained random placement procedure was rejected because it can fail a feasible exact count. Counts are recovered from actual eligible centers; silently clipping them was rejected.

Requested palette sizes are also observable. Colors absent from the motifs appear as singleton markers outside protected centers/arms, so asking for nine colors produces nine nonzero colors without adding an accidental eligible center. Fixing color numbers by motif order was rejected because that couples appearance to semantic role. The finite constructor probe in [checks/code-review/probe.json](checks/code-review/probe.json) covers heights/widths 5..14, counts 1..6, palette sizes {1,9}, and seeds {0,17} with difficulty omitted: 2,092 exact accepted realizations and 308 expected capacity rejections among 2,400 requests, with no unexpected finding. It is a structural probe, not a Racket-labelled lesson census.

`self_check` accepts a broader positive-example rule domain: rectangular integer-color grids 3..30 with at least one eligible center. Shared arms, connected positives, and mixed valid/invalid neighborhoods are accepted. Restricting validation to isolated generated motifs was rejected because separation is a construction convenience. [The condition witnesses](repo/generators/6355eb114053/counterexamples/condition_witnesses.json) retain actual selected-Racket outputs for direction mismatches, shared-arm positives, and an occupied-center case; [checks/selected-counterexamples-racket.json](checks/selected-counterexamples-racket.json) retains the public application evidence.

This sampler does not cover every packing admitted by the rule. Some capacity-rejected requests could fit touching positives; that is documented, rather than silently treating the constructive family as the complete semantic domain. No-change grids remain outside its positive-example validator despite having defined Racket outputs. Border-only negatives and touching-positive families are not separately scheduled production profiles. The layout distribution is not uniform over all packings.

## Contrastive teaching schedule

Ordinary draws include true positive pluses, a missing-arm neighborhood, a different-color-arm neighborhood, and four matching arms around an already occupied differently colored center. Even indices omit north and mismatch south; odd indices omit west and mismatch east. Roles can share colors, and motif locations are shuffled. This supplies direct contrasts for both opposite-direction rivals, each omitted cardinal condition, majority-of-three, equality-blind filling, and overwriting existing centers. Adding only more isolated true pluses was rejected because those examples preserve the old north/south shortcut. Purely independent random decoy choices were rejected because a short lesson could omit a needed direction.

`EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=2`. A four-pair nominal window has both phases twice, so holding out any one pair leaves both phases among its three demonstrations. The intended production policy is three ordered demonstrations followed by one query, and all four query holdouts are supported by the tested ordinary distribution. The actual accepted/materialized pairs, rather than an assumed nominal schedule, were checked in the public census. Palette size one cannot exhibit equality mismatch or a differently colored occupied center; small explicitly forced canvases can lack room for all three decoys. Those controls remain exact and have no ordinary-lesson identifiability guarantee. A global passing battery does not confer that guarantee on an arbitrary overridden lesson.

The retained Racket-labelled census reports production **no ambiguity found, 300/300 lessons**, and query rotations **no ambiguity found, 1,200/1,200 holdouts**, covering 1,200 unique inputs, 100 lessons per band, requested starts 0..99, and the report's deterministic `sha256('lesson-census:v1:TASK:BAND:INDEX')[:8]` seed recipe. The separate fixed-seed census enumerates starts 0 and 1 at seed 0 in each band: production **6/6** and rotations **24/24**, with **6 unique inputs** across overlapping lessons. Both reports check nine unique executable rivals; the repeated declarations under three contract names are not 27 independent hypotheses. These finite results establish the reported declared-rival verdicts, not uniqueness against arbitrary programs or all seeds. Exact reports and accepted-index histories are in [lesson-census.json](checks/lesson-census.json) and [schedule-census.json](checks/schedule-census.json).

## Failures retained and final verification

The focused baseline run genuinely failed 41 tests and passed 21; it is preserved in [checks/red-focused.log](checks/red-focused.log). The first rewrite used a positional argument where `draw_distinct_colors` requires keyword `n`, causing 40 failures and 22 passes in [checks/green-focused-v1.log](checks/green-focused-v1.log); the API call was corrected. The alias-as-fifth-axis iteration failed lint and override provenance before the four-axis correction. Initial public task-test preflight found pytest missing in the selected interpreter, so no source was staged and no tests ran; [checks/task-tests-console.log](checks/task-tests-console.log) records that environment failure. A review virtual environment supplied the prerequisites, and the final public task-test report records 62 passes.

The final source has **12/12 green battery stages**, including required query rotations, and no failed/advisory stages in [checks/after-final/checks/6355eb114053_after_battery_summary.json](checks/after-final/checks/6355eb114053_after_battery_summary.json). These task-local checks, structural probes, and lesson censuses are the basis of the claims here. Wider repository diagnostics and final portable handoff checks are recorded separately by the coordinating reviewer; this report makes no new wider-suite conclusion.

## Self-review and shared follow-up

The repair removes fixed position/color role cues and tests three contrasts that would refute the old shortcut; it retains documented packing and explicit-override teaching limits. The finite selected-Racket witnesses and actual lesson censuses support the declared-rival claims, while unusual overrides and undeclared hypotheses remain outside that certification.

Task-local fixes are included. The highest-priority shared request is **F1**, admission-time scoring of each actual exported lesson against declared rivals, with source-bound per-episode evidence; existing authoring diagnostics already supply the necessary scorer. **F2** is optional shared alias metadata/tool support, while the task-local alias correction is already included. See [FEEDBACK_TO_CODEX.md](FEEDBACK_TO_CODEX.md).

Retained prior-return ZIP identities and source bindings are listed in [checks/inherited-evidence-provenance.json](checks/inherited-evidence-provenance.json) and the prior-finding table in [REVIEW.md](REVIEW.md).
