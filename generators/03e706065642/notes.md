# Current account: 03e706065642

## Intended rule

Find the three color-1 frames from left to right.  For each framed monochrome motif,
binarize its tight bounding box and classify reflection symmetry as: neither (0),
left/right only (1), up/down only (2), or both (3).  Return a 3×3 matrix containing
2 exactly when the corresponding motifs have the same symmetry class, otherwise 0.
Motif color and exact shape are distractors.

The canonical authority remains pinned by `RULE_HASH = "ae585f1eb109"`.  Its
executable behavior was not changed.  The duplicate bank `racket_target.target_code`
was made byte-for-byte identical to `raw_code`; this removed source drift only.

## Defect and repair

The imported 2.3.0 generator omitted a rule hash, did not expose a semantic teaching
contract, missed the canonical 9×23/three-color profile, silently accepted unknown
overrides, and advertised controls that were inert or band-limited.  Version 3.0.0
replaces those controls with three exact, observable, orthogonal axes:

- `frame_n`: 5, 6, 7, or 8 in every difficulty band;
- `layout`: pair, all-same, or all-distinct symmetry classes;
- `texture`: one shared motif color or three distinct motif colors.

Invalid values and unknown keys raise `ValueError`.  `observe_overrides` recovers the
three values from the returned grid.  A default sample at schedule slot 0 recurrently
uses the canonical 9×23 profile while other slots broaden frame size, spacing, motif
size, shape, and palette.

## Curriculum and shortcut control

Lessons use five deterministic semantic slots and four demonstrations plus one query.
The first three class triples are `(2,2,0)`, `(1,3,1)`, and `(0,2,2)`; the remaining
slots cover all-distinct and all-same layouts.  This deliberately supplies two
independent vertical-only witnesses.  The canonical examples contain no vertical-only
motif, so the rival that collapses class 2 into class 0 fits every canonical pair.
A Racket-labelled lawful witness is retained at
`counterexamples/collapse_ud_with_none.json` and covered by a focused test.

Declared executable competitors are:

- collapse up/down-only symmetry into no symmetry;
- compare exact normalized shapes instead of symmetry classes;
- compare motif colors instead of symmetry classes.

`lesson_identifiable` requires all four demonstrations to be lawful, correctly labelled,
and to refute every declared competitor.  The five-slot schedule makes every cyclic
four-demo holdout and every query rotation refute all three declared rivals.

## Structural choices

Generated inputs retain the canonical composition: exactly three disjoint, horizontally
aligned, hollow color-1 square frames with one monochrome nonempty motif per frame.
Same-class motifs are not exact duplicates; all-same-class grids use at least two exact
shapes.  Large frames can contain motifs spanning at least four rows or columns.
`self_check`, `strict_canonical_like`, `analyze_grid`, and `rule_mirror` are deterministic
and input-pure.  The exact output codomain is the five equality partitions of three
items (Bell number B3).

## Verification and limits

Final generator SHA-256:
`7f9c01a709cc923a4c9cd2c17a25065895d5dc1773c722e2f411bef306c8719c`.
The source-bound after battery completed 12/12 green stages with required query
rotations.  The task-local suite completed 23/23.  A 300-lesson census (100 per band)
materialized 1,500 ordered pairs and 1,500 query rotations with zero ambiguity against
the three declared competitors and 1,500 unique inputs.

These finite checks establish the declared contract only; they do not prove universal
identifiability against every conceivable rival.  The generator intentionally does not
vary frame color, frame count, vertical arrangement, multicolor motifs, rotations, or
non-square frames because those changes would broaden the task grammar beyond the
canonical rule's demonstrated composition.  No blocking generator finding remains.

No prior return was available as a repair lead: `evidence/associated_notes.jsonl` was
empty and this task had no retained review index.  The untouched current-source battery
and canonical examples supplied the baseline evidence.
## Current reviewer considerations

Source SHA-256: `7f9c01a709cc923a4c9cd2c17a25065895d5dc1773c722e2f411bef306c8719c`.

# Decisions for 03e706065642

## Scope and evidence policy

The selected task is a per-puzzle generator for a fixed canonical Racket rule.
`evidence/associated_notes.jsonl` was empty and no retained review index existed,
so there was no prior return to adopt as authority.  The untouched generator,
canonical examples, and `checks/before/` are the baseline.  Failed tests and
intermediate checks were retained rather than overwritten.

The canonical rule itself was not semantically changed.  I treated it as the
binding definition and changed the sampler, executable contracts, tests, notes,
and one duplicate selected-source field.  Final generator SHA-256 is
`7f9c01a709cc923a4c9cd2c17a25065895d5dc1773c722e2f411bef306c8719c`;
the pinned rule hash is `ae585f1eb109`.

## D1 — Preserve the symmetry-class rule

**Choice.** Keep the four reflection classes exactly as the authority defines
them: neither, left/right only, up/down only, and both.  Compare the three class
values to form a 3×3 matrix of 2s and 0s.

**Rationale.** All five canonical labelled pairs agree with that interpretation,
and the baseline rule smoke already passed.  The defect was distributional and
contractual, not a wrong canonical program.

**Alternative rejected.** Changing the Racket rule to exact-shape equality,
color equality, or a three-class scheme would contradict canonical outputs.

**Probe.** `rule_mirror` is checked against every canonical pair and the selected
Racket authority.  The public battery's rule-smoke and authority stages are green.

**Failure mode if wrong.** A Python/Racket mismatch would corrupt every generated
label.  The canonical mirror tests and public apply witness make that failure loud.

## D2 — Replace the old advertised controls with three exact axes

**Choice.** Advertise only:

- `frame_n ∈ {5,6,7,8}`;
- `layout ∈ {pair, all_same, all_distinct}`;
- `texture ∈ {same_color, mixed_colors}`.

All values are legal in every difficulty band; unknown keys and invalid values
raise `ValueError`; `observe_overrides` recovers the realized values from pixels.

**Prior choice.** The baseline advertised frame, layout, and four texture values,
but frame values were band-limited, layout became inert in mixed combinations,
no exact observer existed, and unknown keys were silently accepted.  No retained
rationale for those choices was available.

**Rationale.** The replacement axes are independently visible and semantically
meaningful: frame size changes geometry, layout changes the equality partition,
and texture changes only distractor color relationships.

**Alternatives rejected.** Keeping aliases or diagnostic-only axes would preserve
surface variety but not falsifiable controls.  Declaring extensive incompatibility
rules would make the API harder to use without adding task coverage.

**Probe.** The final override stage is green; focused tests enumerate all four
frame sizes in all three bands, every layout with both textures, invalid values,
and unknown keys.

**Known limit.** Difficulty changes sampling weights, not the legal exact domain.
This is intentional so an override means the same thing in every band.

## D3 — Reintroduce canonical geometry recurrently, not exclusively

**Choice.** Default schedule slot 0 uses the canonical 9×23, three-color profile:
three 6×6 frames beginning at row 2 and columns 1, 9, and 17.  Other slots vary
frame size, margins, and gaps.

**Rationale.** The untouched generator hit neither the canonical exact profile nor
its envelope in 60 draws.  Recurrent exact support fixes that gap while retaining
broader geometry.

**Alternative rejected.** Forcing all draws to 9×23 would pass the profile floor
but collapse geometric diversity and make dimensions an unnecessary shortcut.
An opt-out would document the gap rather than repair it.

**Probe.** Each band's 20-draw profile-floor sample now contains an exact canonical
profile.  `strict_canonical_like` remains semantic/structural rather than an exact
dimension predicate, so all lawful broader draws count toward the declared 1.0
strict fraction.

**Failure mode if wrong.** A too-narrow strict predicate would reject intended
variation; a too-broad one could admit unrelated grids.  `self_check`, canonical
admission, and the 600-draw semantic gate jointly constrain this choice.

## D4 — Generate symmetry classes directly, but vary exact shapes

**Choice.** Construct a motif with exactly the requested reflection class, then
verify the normalized shape.  Repeated classes within one input use different
exact shapes.  Frame size 8 preferentially generates larger motifs.

**Rationale.** Same-class equality must not be learnable as pixel identity.  The
canonical examples already show different shapes sharing a class, so generated
pairs need the same distinction.

**Alternative rejected.** Reusing a small fixed motif bank would make exact shape
a strong shortcut and underuse larger frames.  Random cells without post-checking
could accidentally land in the wrong class.

**Probe.** `exact_shape_equality` is an executable rival.  The semantic gate saw
474/600 individual disagreements, and every final lesson refuted the rival.
Focused tests also require three distinct exact shapes in generated all-same cases
and observe motifs spanning at least four rows or columns in large frames.

**Ruling.** A canonical all-same example contains only two distinct exact shapes,
so `self_check` requires at least two there.  Generated all-same draws still use
three.  Making the validator require three would incorrectly reject canonical data.

## D5 — Treat motif color as a distractor axis

**Choice.** Each motif is monochrome.  `same_color` assigns one color to all three;
`mixed_colors` assigns three distinct colors.  The rule binarizes motifs, so color
never affects the answer.

**Rationale.** Showing both extremes prevents a learner from equating color
identity with symmetry-class identity.

**Alternative rejected.** Partially repeated colors would add another layout-like
axis but complicate exact observability without addressing a stronger canonical
shortcut.  Multicolor motifs would broaden the task grammar beyond the examples.

**Probe.** `motif_color_equality` is a declared rival and disagreed on all 600
semantic-gate draws.  Every 300-lesson census window and all query rotations
refuted it.

## D6 — Use a five-slot semantic curriculum with four demonstrations

**Choice.** `EXAMPLES_NEEDED = 4`, with five deterministic semantic slots.  The
first three class triples are `(2,2,0)`, `(1,3,1)`, and `(0,2,2)`; the remaining
slots cover all-distinct and all-same partitions.  A lesson consists of four
demonstrations plus one query.

**Rationale.** Four demos in a five-pair bundle permit every held-out query to
leave enough evidence against all declared rivals.  Slots 0 and 2 are independent
up/down-only witnesses; the other slots separate exact-shape and color guesses and
cover all five equality partitions of three items.

**Alternative rejected.** Three demonstrations are cheaper but allow a query
rotation to remove the only class-2 witness in some windows.  Random independent
layouts can produce semantically weak bundles even when every label is correct.

**Test-plan ruling.** An early test incorrectly demanded the class-2-collapse
rival differ on `(1,3,1)`, which contains no class 2.  That assertion was changed
to require witness slots 0 and 2.  The exhaustive query-rotation test remains the
stronger lesson-level gate.

**Probe.** Task tests check ten consecutive starts in every band and every one of
five query positions.  The source-bound census materialized 300 lessons, 1,500
pairs, and 1,500 hold-one-out rotations with zero ambiguity or scoring errors.

**Known limit.** This establishes identifiability only against declared rivals and
finite sampled starts.  It is not a proof against every possible program.

## D7 — Declare executable rivals and witnesses

**Choice.** Retain three competitors:

1. collapse up/down-only symmetry into no symmetry;
2. compare exact normalized shapes;
3. compare motif colors.

`SEMANTIC_WITNESSES` fires precisely when the corresponding competitor differs
from `rule_mirror`; `WITNESS_RIVALS` maps witness names to lists of rival names;
`lesson_identifiable` validates labels and requires every competitor be falsified
by the demonstrations.

**Rationale.** The first rival fits all five canonical labelled pairs and is the
main unseen-branch shortcut.  The other two capture plausible surface rules.
Executable declarations let shared tooling test claims rather than trust prose.

**Alternative rejected.** A prose-only warning or a witness predicate without a
named rival cannot establish that lesson demonstrations actually distinguish the
hypothesis.

**Intermediate failure.** The first declaration used the wrong `WITNESS_RIVALS`
schema.  A focused failing test exposed it; the corrected witness-name → rival-list
mapping now passes static and semantic checks.

## D8 — Keep the structural validator canonical-compatible

**Choice.** Require exactly three disjoint, horizontally aligned, hollow color-1
square frames; one nonempty monochrome motif per frame; no nonzero pixels outside
frames; all motif colors either shared or all distinct; and non-duplicated exact
shapes for repeated classes.

**Rationale.** These conditions describe the composition demonstrated by the
canonical task while making all advertised axes observable.

**Alternatives rejected.** Varying frame color/count, vertical arrangement,
non-square frames, or multicolor motifs could be accepted by some abstract reading
of the rule but would move beyond the demonstrated grammar and increase object
parsing ambiguity.

**Probe.** All five canonical inputs pass, all final generated draws pass, and
canonical profile plus grammar stages are green.

**Known limit.** The generator intentionally trains only this three-horizontal-
frame composition.  It does not claim the Racket implementation's behavior on
arbitrary malformed or broadened layouts is part of the curriculum.

## D9 — Declare the exact finite output codomain

**Choice.** Set `EXPECTED_OUTPUT_CODOMAIN = 5`.

**Rationale.** Equality matrices for three items correspond to the five set
partitions of three elements (Bell number B3).  The five-slot curriculum reaches
all five, so a low output count is intrinsic rather than a collapse defect.

**Alternative rejected.** Suppressing the lint warning without a mathematical
codomain claim would hide genuine output collapse.  Declaring nine or more outputs
would be false.

**Probe.** The final lint and diversity stages are green, and focused schedule
tests exercise all partitions.

## D10 — Synchronize duplicate selected rule text without changing behavior

**Choice.** Make the selected bank record's `racket_target.target_code` exactly
match its `raw_code`.  No canonical ledger row or executable Racket behavior was
changed.

**Rationale.** Baseline authority sync found two active exact-text groups even
though execution parity passed.  Maintaining two active textual authorities is a
future drift risk.

**Alternative rejected.** Changing the canonical program was unnecessary.
Leaving the divergence as “beautification” would keep the required authority gate
red.

**Probe.** The final authority-sync stage is green; rule hash remains
`ae585f1eb109`; the retained Racket counterexample output matches the Python mirror.

## D11 — Retain a minimal source-bound counterexample

**Choice.** Keep
`repo/generators/03e706065642/counterexamples/collapse_ud_with_none.json`, derived
from seed 73, sample index 0, medium difficulty.

**Rationale.** It is a compact lawful instance with classes `(2,2,0)` where the
strongest canonical-fitting shortcut returns an all-2 matrix but the authority
returns two equal vertical-only motifs and one distinct no-symmetry motif.

**Probe.** The public Racket apply report is
`checks/main-counterexample/racket.json`.  The focused test was observed failing
before the artifact existed and passing afterward.

## D12 — Verification and stopping rule

**Choice.** Stop after the final source-bound battery, portable task tests, wide
lesson census, fresh exposed solve, and two assigned audits were complete.

**Measured final evidence.** The after battery is 12/12 green; task tests are
23/23; the 300-lesson census has zero production or rotation ambiguity against
declared rivals; the fresh solve passes 4/4 visible examples with private query
labels withheld.

**Remaining limitations.** Declared-rival checks are finite; exact frame grammar is
narrower than every input the abstract Racket program could process; and the
battery controller required hash-verified resumes after orchestration stalls.
Those limitations do not leave a blocking failure in the selected generator.
