# Current notes: 7f03452e81df — crop the smallest object

## Rule and authority

Use same-color, four-neighbor connected nonzero components on background zero.
Choose by (cell count, top row, left column), then crop the original grid to
the chosen component's inclusive bounding box. Preserve every original cell
inside that box, including disconnected foreign-colored objects. The canonical
Racket authority is unchanged; normalized RULE_HASH remains `677cf77c7816`.

## Current distribution — version 3.1.0

Keep the five semantic profiles and their existing component-count/size/box
obligations: canonical anchor, repeated sparse target color, nested crop, row
tie, and column tie. Their seed-phased semantic schedule has period five.
Each scene uses one of the canonical 8×10, 9×11, or 10×12 canvases and background
plus three distinct foreground colors. Difficulty changes schedule phase; it is
not a validated monotonic measure of reasoning complexity.

Components receive bounded connected-shape proposals, square symmetries, and
new positions. Nested target and interior object move together under a symmetry
to preserve the foreign-cell crop witness; their internal structure remains
narrow. Components in different placement groups cannot overlap or touch along
an edge. Exact `scene_profile` overrides remain observable and validated.

## Reversal of the fixed-template choice

The inherited July 28 notes explicitly deferred geometry expansion, prioritizing
the five teaching witnesses. On the pinned v3.0.0 source, a 50-seed panel had
exactly one palette-normalized scene and one selected bounding box per profile.
More seriously, a query five draws after the first demonstration was always its
exact recoloring: a demonstration-copy rival solved 60/60 tested lessons without
doing object selection. This makes geometry expansion necessary for training use.

The current implementation keeps the semantic obligations but varies geometry
and placement. Canonical canvas selection changes between same-profile draws
five indices apart, removing guaranteed exact demo-copying in an unrejected
five-demo lesson. The same panel now has 50 distinct normalized scenes per
profile (250/250 total); the copy rival applies to 0/60 tested repaired lessons.
Reproduce with `workspace/probe_distribution.py`; its bulk labels are explicitly
the selected Python mirror. The return's Racket witness receipt independently
checks the decisive before/after lesson and the validator counterexample.

## Validator and teaching repairs

`sample_index` must be a nonnegative integer and cannot be a boolean. The old
generator accepted bool, float, string, and negative values; regression tests
now retain all five failing cases. The lesson hook validates labelled evidence
and actual rival disagreement, instead of indexing the strict profile observer.
`counterexamples/non_template_tie.json` is lawful with sizes [5,5,7] and exposed
the old KeyError. Its reference output is unchanged and Racket-verified.

## Teaching policy and measured limits

Default policy is five ordered demonstrations followed by a query. The final
source passed all 300 production lessons (100 per band, 1,800 unique inputs)
against the declared rivals, and all 15 fixed-seed/start-residue lessons at seed
0. These are finite rival checks, not a proof of universal identifiability.

Arbitrary query rotations are unsupported with five demos: 769/1,800 measured
rotations are ambiguous. For a consumer needing such rotations, the explicit
nine-demo setting covers two full profile cycles before a single-pair holdout;
all 150 tested rotations across the 15 fixed-seed starts passed. The default
stays at five to avoid imposing the extra four demonstrations on ordered use.
Rejected/duplicate sample indices can alter an accepted lesson schedule, so use
the production materializer and retained census, not only raw index arithmetic.

Shape/placement search is bounded (24 shape proposals, 128 scene proposals,
40 positions per group); exhausted scene construction raises clearly. Finite
testing found no ordinary-generation failure, but does not certify every seed.
Fixed size signatures and canonical canvas support still restrict the domain.

## Verification and open tooling issue

Twenty focused task-test cases pass in both direct and isolated runtime layouts;
13 newly authored cases failed against the baseline before the repair. Final
Racket smoke has 120/120 applications and mirror agreements; exact-control
checks have 540/540 accepted draws and no findings; strict support has 600/600
hits and all three canonical pairs accepted.

The raw final battery remains 11/12 green because its semantic stage emits
`declared_period_not_enumerated` for every positive period declaration, without
an input for the separately completed census receipt. The retained fixed-seed
receipt has complete coverage on these exact generator bytes. Do not remove the
honest period declaration or relabel the raw battery as passing to hide this
tool limitation. It is a maintainer attention item, separate from the documented
five-demo rotation limitation. No earlier unresolved audit index was present for
this selected task; unrelated audit targets retain their own findings.
## Current reviewer considerations

Source SHA-256: `82d4d1f6ff25817f3c45ceca47c04e0926d0651f92d319e9c3f07ff09f0bcba9`.

# Repair decisions — 7f03452e81df

## Scope and source

Assignment `review-7774f6a24c5845ee` retained its original draw. Baseline generator
SHA-256: `626a29e228700b0ff6e1cefcd88ff59ccde9f45ee487c4c4d16cf079bc684538`.
Final v3.1.0 generator SHA-256:
`82d4d1f6ff25817f3c45ceca47c04e0926d0651f92d319e9c3f07ff09f0bcba9`.
The Racket rule, canonical examples, shared tools, and audit-target sources were
not edited. The generator's current notes contain the maintained decision account.

## D1 / R1: replace palette-only template variation

The inherited associated note `GNOTE-003860` from
`external-local-random:ca9cb04ba94a` explicitly identifies fixed geometry as a
limitation. It was a lead, not evidence of current behavior. Fresh measurements
in `checks/distribution-before.json` establish one geometry per profile and a
60/60 demonstration-copy shortcut. A five-profile period and five demonstrations
made each query a recoloring of its first demonstration.

The repair varies connected polyominoes within each seed object's count and tight
box, square symmetries, component placement, and all three canonical canvases.
It preserves the nested pair as one group, aligns column-tie minima at one row,
and rechecks all semantic obligations after placement. The canvas phase changes
after each five-index block; same-profile demonstration and query dimensions
therefore differ in an unrejected six-draw window.

Rejected alternatives: adding only palette entropy leaves the shortcut intact;
global translation/reflection alone preserves too much template structure;
unconstrained shape/random-object generation risks losing the deliberate bbox,
frequency, crop-preservation, and tie witnesses. The chosen construction is a
bounded expansion of the existing teaching domain. It does not claim unrestricted
polyomino or canvas support. Nested internal geometry and fixed profile size
signatures remain limitations.

The matched 250-draw panels now show 250 normalized input layouts versus five;
the retained copy rival can copy 0/60 repaired queries versus 60/60 before.
`checks/distribution-after.json` retains the exact panel, counts, source identity,
and one lesson. `checks/authority-witness-racket.json` independently labels the
decisive baseline/repaired lessons and non-template counterexample (13 grids).

## D2 / R2: validate integer sample indices without silent coercion

The baseline defect linter reproduced acceptance of `True`, `False`, `1.0`,
`"1"`, and `-1` for sample_index. All five newly authored regression cases failed
before the change. Scheduling now rejects non-int values, booleans, and negative
indices before constructing the random context. Normal integer semantics and
the existing scene_profile axis remain unchanged.

## D3 / R3: teach from actual labels, not exact template signatures

The old lesson hook called the broad validator but indexed the stricter override
observer. Removing one cell from the tie_col distractor produces a lawful,
strict-canonical-like [5,5,7] scene for which that observer returns no profile;
the old hook raised `KeyError`. The retained
`repo/generators/7f03452e81df/counterexamples/non_template_tie.json` includes exact
old generation settings and the mutation.

The hook now checks label agreement and refutes each actual declared competitor.
This accepts alternative valid witnesses and returns reasons for under-taught
lessons, without making the observer a lesson-domain oracle. The broad validator,
strict support definition, and exact-control observer keep their distinct roles.
No frozen root fixture was changed. Existing task-local tests were migrated to
the documented portable helpers; new tests live in the assigned tests directory.

## D4: five ordered demonstrations; rotations require additional evidence

The default remains five demonstrations in production order, one query. The
300-lesson production census has zero declared-rival ambiguity, zero hook
warnings, and zero errors across 100 lessons per band / 1,800 unique inputs.
Its 1,800 rotations include the original query positions and are not independent
new samples; 769 are ambiguous. The seed-0 exhaustive profile-start census checks
15 overlapping lessons / 90 rotations over 30 unique inputs; production is clean
and 36 rotations are ambiguous.

Increasing the default to nine demonstrations would cover two complete profile
cycles across the ten labelled pairs but adds four examples to every ordered
lesson. Instead, an explicit `--train 9` census tests that optional assembly:
15 lessons / 150 rotations, zero ambiguity or errors, 42 unique inputs. It checks
all five declared starts in all three bands at seed 0, not all random seeds.
Consumers must retain the assembly policy in their training metadata.

## D5: retain the truthful period declaration and raw check warning

`LESSON_SCHEDULE_PERIOD = 5` enables the required independent enumeration. The
current semantic gate unconditionally warns for a declared positive period and
cannot read a supplied completed schedule census. Its after-phase strict exit
therefore fails despite 12/12 sampled lessons, all six rival claims, and the
separate complete fixed-seed receipt. The raw battery remains 11/12 green.
Removing the declaration solely to obtain a green receipt would conceal useful
information; modifying shared sources is outside this repair. F1 documents the
needed tool change and exact corroborating evidence. Acceptance needs attention
for this narrow tool/reporting decision and the stated rotation policy.

## D6: preserve unsuccessful checks and solve provenance

The baseline battery and 13 failing regressions remain in checks/. The first
isolated task-test attempt stopped before staging because pytest was only in the
user site. A local venv with pytest installed under PYTHONNOUSERSITE=1 fixed the
prerequisite without weakening isolation; all 20 cases then passed with no skips.
The general repository test run and any independent failures remain separately
reported rather than being conflated with task-local success.

The blind solve finished before source inspection and passed 3/3 visible pairs
in one genuine revision. The post-repair solve is bound to the final generator,
discloses earlier exposure, and passed 5/5 visible pairs in one genuine revision.
Both hidden-query labels remain unknown here. Work logs are reviewer-authored
summaries, not token-level traces. No negative solve was manufactured.

## Self-review

The repair removes the measured exact-copy shortcut while retaining every
declared witness, Racket authority, legal color role, and canonical support.
It still has a deliberately narrow size grammar and does not establish arbitrary
rotation safety or universal success of its bounded placement search; these
constraints and finite denominators are explicit above and in the current notes.
