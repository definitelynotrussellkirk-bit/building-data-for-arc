# Working notes: 20859a33c80e

## Review 088fbb6f91283037 — version 3.1.0

**R1: complete lessons must distinguish components from colors.** Version 3.0.0
scheduled five distinct-color draws followed by five repeated-color draws.
Consequently, a consecutive five-demonstration lesson could establish every
scene profile but leave a wrong global-color object model unchallenged before
a repeated-color query. The global-color rival fits all four canonical pairs.
The pre-repair local census found 60 accepted ambiguous lessons among 600
windows (20/200 in each band); a six-pair public Racket receipt corroborates
one counterexample. Individual witness frequency and the old all-green battery
did not establish complete-lesson identifiability.

Version 3.1.0 alternates color patterns at period two while keeping the five-scene
schedule. Every consecutive five-demo window now contains both color patterns;
each scene still receives both over ten draws. Register global-color grouping
and a depth-three cap as actual canonical-fitting rivals. Keep the existing
incorrect rules as general lesson competitors, rather than claiming that they
fit all canonical examples. Tie the repeated-color witness to the new rival.

**R2: malformed lesson pairs are validation failures, not exceptions.** Return
recorded validation/profile/output reasons before executing competitor solvers.
A ragged demo previously reached the rival loop and raised IndexError.

**R3: canonical profiles need joint support, not lucky independent draws.**
The first repair changed the keyed random stream with its version bump. Although
input-domain and lesson tests passed, canonical exact-profile hits fell from
8/60 before repair to 2/60, with zero hits in medium and hard. Add a joint 11x11
anchor on sample indices divisible by seven. This is a deterministic curriculum
choice, not seed search; seven is coprime to the ten-position semantic/color
cycle, so all scene/color combinations receive anchors over seventy draws.
Explicit height/width overrides still take precedence. Other draws retain the
original difficulty-skewed size choices. Final battery profile hits: easy 3/20,
medium 4/20, hard 4/20. The source and command receipts are in the review delta.

## Authority and domain

The canonical RULE_HASH remains `c7c12a48b62f`; no Racket or authority files changed.
Normal draws still contain four components, one or two roots, and maximum depth
2–4. Validators intentionally accept a broader range than the normal curriculum.
Do not infer that depth-five-plus or arbitrary shapes are taught by this patch.
Do not treat passing review checks as training approval.

Prior lead: `evidence/associated_notes.jsonl`, review `local-random-ea4c1b0e6c43`
(worker `external-local-random:ea4c1b0e6c43`), references
`review_response_ea4c1b0e6c43_x/RESULTS.json`. Its return ZIP and SHA were not
available here. GNOTE003675 supports bbox-depth authority; GNOTE003677 describes
existing witnesses; GNOTE003679 cautions against unsupported depth expansion.
These notes informed hypotheses, not current-source test claims.

## Reusable checks

Run `workspace/lesson_probe.py` for all ten cyclic starts and dynamic rival
registries; it is a census and returns zero even when it reports ambiguity.
Run `workspace/verify_public_lessons.py` for actual `Catalog.generate` lessons,
Racket outputs, source hashes, accepted sample indices and rival survival. It
fails on detected semantic errors and requires explicit research opt-in.
See `workspace/README.md` for exact commands and limitations.
## Current reviewer considerations

Source SHA-256: `42247ae6adaefbdefddf023835b2ccdd83e71060c2ab1d0364f1be9afd7b885d`.

# Decisions — review-088fbb6f91283037

## Inputs and prior rationale

Read the assigned generator, frozen fixture, existing workspace, canonical task
pairs and rule, and associated notes only after completing the separate blind
solve. The packet baseline is authoritative; no unintegrated prior patch was
assumed to exist. Prior lead: review `local-random-ea4c1b0e6c43`, worker
`external-local-random:ea4c1b0e6c43`, named return directory
`review_response_ea4c1b0e6c43_x/RESULTS.json`. Only its associated notes are included;
the earlier return ZIP/hash is unavailable, so no old test result is presented as
a fresh measurement.

GNOTE003675 identifies bbox-depth authority rather than an older unrelated
frame-pairing explanation. GNOTE003677 explains boundary, non-frame, deep and
repeated-color witnesses; GNOTE003679 cautions against unsupported depth expansion.
The baseline implements that intended grammar substantially correctly. Preserve
its canonical rule, five semantic scenes, geometry helpers and exact axes rather
than replace the task with a superficially similar one.

## R1 — choose lesson coverage rather than more random draw coverage

Observed: the baseline battery passes 12/12; each witness fires, but the pattern
schedule is five distinct-color draws then five repeated-color draws. A local
census exhausts ten scene/color starts per seed and finds 20/200 accepted ambiguous
five-demo/one-query windows per band. The independent global-color competitor fits
all four canonical pairs. A six-pair supported Racket apply corroborates the first
saved counterexample at seed 0, easy, start 0, query index 5.

Decision: alternate at period two, retaining the period-five scene schedule.
This gives both patterns in every five-demo window and both patterns for every
scene in ten positions. Register global-color grouping and depth-three capping;
retain the other rivals as lesson competitors but remove their inaccurate
canonical-fitting declarations. Wire witnesses to actual distinguishing rivals.

Rejected alternatives: add more samples without changing assembly (preserves the
same missing counterexample); force repeated colors on every draw (needlessly
narrows the domain); only reject bad lessons (could waste sampling and offers no
coverage guarantee); randomize color patterns without a deterministic coverage
constraint (permits the same failure); rewrite reference outputs (wrong authority).

Tests first: seven failures among 34 tests on baseline reproduce registry,
lesson and malformed-input defects. After the minimal repair, 34/34 pass, and the
same census yields zero ambiguous lessons. Final tests additionally cover anchors.
Tools iterate actual declarations; the standalone diagnostic is deliberately
independent so an omitted registry entry cannot hide the original defect.

## R2 — fail validation before rival execution

A malformed ragged demo produces a validation reason but the old function keeps
going into rival solvers and raises IndexError. Return accumulated reasons after
validating demos/query and before asking competitors to consume them. Preserve
existing profile requirements and output-consistency checks. A regression calls
the real hook with one ragged demo and expects reasons, not an exception.

## R3 — joint canonical-size anchors

The initial v3.1.0 source changes the version-keyed random stream. Independent
height/width choices then yield only two exact canonical profile hits in sixty
battery draws, with medium/hard exact hits both zero; this is not repaired by
passing morphology-envelope checks. Do not hunt for seeds or repeatedly change
versions until the gate happens to pass.

Choose 11×11 on indices divisible by seven: it is supported by two canonical
size/palette profiles, is valid for all existing scenes, and seven is coprime to
five scenes times two palettes. A 70-position test explicitly covers every
scene/color pair under the anchor. Non-anchor draws preserve the original
band-skewed sizes; explicit dimension controls always override the anchor.
The three new anchor tests fail before the change (3 failed, 34 passed), then
all 37 focused tests pass. Final profile counts are 3/20, 4/20 and 4/20.

Rejected alternatives: fix every draw at canonical size (destroys size diversity);
change only one marginal probability (joint support remains fragile); tie anchors
to one scene index (creates a fixed scene-size association). The chosen periodic
size prior is still a limitation and causes some cross-band duplicate inputs;
measure and report those instead of calling all occurrences unique.

## Preserved failures and iteration identities

Baseline SHA: `ce58afdc9309551c49486b578697e18f4504f2cb6e93f023032f6dc76ce56560`.
First repair SHA: `9e9396440d3c6b41bfd759fac54008ab9e92f74c0a511fa76c0f6668a0855cf7`.
Its battery reports a lint warning (`objects`, a local name inside the deliberately
wrong rival, shadows a DSL primitive) and profile-floor failure. Rename that local
to `grouped_components`; do not suppress the linter or change the rival's meaning.
Second repair SHA: `31c44730b9b73be935fab300ac275f0c4786e1005865b8a7122976de3d7bf3c6`.
Lint is then clean, but profile support remains failed. Misleading earlier filenames
containing `final` refer to this intermediate and are explicitly indexed as such.
Final SHA: `42247ae6adaefbdefddf023835b2ccdd83e71060c2ab1d0364f1be9afd7b885d`.
All failures remain under checks, and all final-source claims point to `checks/final`,
`*-final2` or the explicit final lint output, not an intermediate directory.

## Actual sampling, controls and final stopping criterion

Local census: seeds 0–19, indices 0–14, ten overlapping starts, all three bands;
600 windows from 900 occurrences, 763 unique final inputs. This exhausts the
scene/color starts, not the full joint size-layout distribution. A separate
70-index test covers the anchor mapping. Real API: 100 seeds per band starting
1000, six pairs per episode, index 0, no rejections; 1,800 Racket pairs and 1,570
unique inputs. Passing finite rivals is not universal identifiability.

Keep the existing advertised exact axes and validator breadth. No equal-box,
deep-five-plus, arbitrary component-count, rotated-family or new background
expansion is justified by this repair. Leave audit targets and shared sources
unchanged. Check the root suite separately, explicitly run focused and frozen
tests, and require fresh exact-delta application before acceptance.

No Qwen model was trained or evaluated. Catalog approval stays false/research-only.
Both solve episodes retain one genuine attempted solution each; visible correctness
is measured and masked correctness remains unknown. Work logs summarize hypotheses
and probes rather than claiming hidden reasoning traces.
