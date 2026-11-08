# Working notes: 5782a1f38509

## Baseline reviewed

Baseline generator SHA-256:
`6dd034f27bdfe9143742b5dca2bd1971783c01633eadeacc240509d0ad03f3bd`.
It produced diverse-looking random blobs but did not pin `RULE_HASH`, declared
single-token/dead axes, had no executable semantic contract, accepted unknown
controls, and did not guarantee canonical support or lesson-level shortcut
refutation.  The initial aggregate battery was interrupted while entering
`dist_gate`; the completed stages still established blocking lint and defect-lint
failures.  Isolated baseline checks additionally found zero strict hard-band
canonical-profile support and 10,696 override findings over 32,580 draws.

## Selected repair

The generator was rebuilt around five constructive profiles rather than a broad
uncontrolled blob sampler.  Each profile isolates a teaching obligation:

- `canonical`: canonical scale and canonical area/shape patterns;
- `order_conflict`: makes area order disagree with position, color, dimensions,
  and descending-area rules;
- `bbox_metric`: separates occupied-cell area from bounding-box area;
- `alignment_gap_shape`: exposes top alignment, one-column separators, and
  preservation of holes in a crop;
- `shared_color`: makes disconnected same-color components distinct objects.

The schedule is `sample_index % 5`, so every consecutive five-example lesson
contains all profiles.  `grid_h`, `grid_w`, and `texture` are the only public
axes.  Exact dimension overrides use their complete advertised ranges; unknown
keys, booleans, invalid types, invalid values, and undersized profile requests
are rejected explicitly.

The canonical rule was not edited.  `RULE_HASH = "a6b584fba994"` pins the
selected authority.  `rule_mirror`, `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `lesson_identifiable` make the teaching claims
executable while leaving Racket as the production label source.

## Iterations retained

1. New task tests were written first and failed 11 cases against the baseline
   (`checks/tdd-red-generator-tests.log`).
2. The first repaired implementation passed its tests but lint flagged a local
   identifier that echoed a Racket primitive; it was renamed without changing
   behavior.
3. The first strict profile-floor run found only 10/60 canonical-profile hits
   (16.7%), below the required 25% floor.  A failing regression was added, then
   `order_conflict` was also placed at canonical dimensions.  The final gate is
   23/60 overall with nonzero support in every band.
4. The lesson probe test initially failed because no source-bound probe existed
   (`checks/tdd-red-lesson-probe.log`).  `workspace/lesson_probe.py` was then
   added and tested.

## Final measurements

Final generator SHA-256:
`33b55d45fe56b2e9493a518ae651cb517a939a3859cd81dc9ec53af8c9cd3d84`.

- Aggregate battery: 12/12 stages green.
- Task-local tests: 18/18 passed in the staged portable runtime.
- Rule smoke: 120 applications, 0 crashes, 0 identities, 40 distinct outputs,
  and 120/120 Python-mirror parity checks.
- Profile floor: 23/60 exact canonical-profile hits; easy 8/20, medium 8/20,
  hard 7/20; all three canonical inputs accepted.
- Semantic gate: 261/600 strict canonical-like draws (43.5%); 6/6 witness
  families fired with verified rival disagreement; 12/12 sampled lessons were
  identifiable.
- Override gate: 35,100/35,100 accepted draws over 390 cases, zero findings,
  zero warnings, and unknown keys rejected.
- Source-bound lesson probe: 300/300 lessons identifiable, 1,669/1,800 unique
  inputs, 808 unique outputs, and all five cyclic schedule starts checked.

## Remaining limits

The constructive curriculum intentionally fixes the domain to exactly three
objects with distinct areas.  Equal-area tie behavior and variable object count
are outside this task's observed canonical contract.  The declared rival set is
broad but finite; lesson identifiability means none of those named rivals
survived, not that universal induction was proved.
## Current reviewer considerations

Source SHA-256: `33b55d45fe56b2e9493a518ae651cb517a939a3859cd81dc9ec53af8c9cd3d84`.

# Decisions for 5782a1f38509

## D1: Keep the canonical Racket rule unchanged

**Decision.** Pin `RULE_HASH = "a6b584fba994"` and repair the generator only.

**Reason.** The canonical pairs and program consistently specify same-color
4-components, tight crops, ascending occupied-cell area, top alignment, and one
blank separator column.  Baseline rule smoke already executed without crashes;
the defect was the data generator and its contract, not the authority.

**Alternative rejected.** Rewriting or normalizing the Racket rule would add
unnecessary authority risk and make generator evidence harder to compare.

**Failure mode controlled.** A stale or silently divergent selected rule now
fails the rule-hash or authority-sync checks.  One archival source remains
divergent but selected-source execution parity passes.

## D2: Use a five-profile deterministic curriculum

**Decision.** Map `sample_index % 5` to `canonical`, `order_conflict`,
`bbox_metric`, `alignment_gap_shape`, and `shared_color`.

**Reason.** A lesson assembled from any five consecutive examples receives one
instance of every teaching obligation.  This is stronger and easier to audit than
hoping random blobs happen to refute each shortcut.

**Alternatives rejected.** Pure random shapes were diverse but semantically
uncontrolled.  Weighted random profile choice could leave short lessons without
critical witnesses.  A larger schedule was unnecessary for the observed rule.

**Failure mode controlled.** The lesson probe tests all cyclic starts and reports
profile counts.  The limit is that downstream samplers that discard or reorder
examples may not preserve the same guarantee.

## D3: Reserve two of five profiles for canonical-scale support

**Decision.** Both `canonical` and `order_conflict` use alternating 5x6 and 5x7
canonical-size footprints by default.

**Reason.** The first repaired version used only one canonical anchor per five
profiles and failed the profile threshold at 10/60 (16.7%).  Moving a second,
still-adversarial profile to canonical dimensions raised final support to 23/60
and preserved every rival witness.

**Alternative rejected.** Lowering the gate or claiming a hard-band opt-out would
hide a real support gap.  Making all profiles canonical-size would reduce useful
scale variation.

**Failure mode controlled.** Exact support is measured independently in every
band.  Canonical dimensions do not imply canonical morphology; the strict hook
also checks colors and area signatures.

## D4: Expose only controls that are observable and exact

**Decision.** Public axes are `grid_h`, `grid_w`, and `texture`.  Unknown keys,
invalid types, invalid domains, and too-small dimension/profile combinations are
rejected.  `observe_overrides` exposes exact returned dimensions.

**Reason.** The baseline advertised numerous singleton or dead axes and accepted
controls it did not honor.  A smaller honest interface is more useful than a
larger cosmetic one.

**Alternatives rejected.** Keeping compatibility aliases would preserve the
baseline ambiguity.  Silent clamping would make exact-control tests meaningless.

**Failure mode controlled.** The final exhaustive override gate covers 390 cases
and 35,100 accepted draws with no findings or warnings.  Some valid dimensions
are incompatible with some profiles; those requests fail explicitly instead of
silently changing the requested size.

## D5: Make semantic claims executable

**Decision.** Add a Python mirror, 12 named rivals, six witness families, two
canonical-fitting shortcuts, and `lesson_identifiable`.

**Reason.** Grid diversity alone cannot show that examples teach the intended
rule.  In particular, `sort_by_height` and `group_by_color` fit every canonical
pair, so generated counterexamples are necessary.

**Alternatives rejected.** Prose-only claims and a copied rival-name list are easy
to drift.  The probe imports the selected generator and calls the functions it
actually declares.

**Failure mode controlled.** The semantic gate verifies witness/rival
disagreement against the mirror, while rule smoke independently establishes
120/120 mirror parity with Racket.  The finite rival list remains an explicit
limitation.

## D6: Keep exactly three objects with distinct areas

**Decision.** Preserve the canonical object count and exclude equal-area ties.

**Reason.** All canonical examples contain three objects and strictly distinct
occupied-cell counts.  The authority's sort behavior on ties is not taught, so
adding tie cases would inject an arbitrary convention.

**Alternatives rejected.** Variable object counts and equal-area objects could
increase superficial diversity but would widen the domain beyond evidence.

**Failure mode controlled.** `self_check` enforces object count, separation,
area uniqueness, and output size.  The documented limitation is reduced domain
breadth, not an unnoticed bug.

## D7: Include disconnected objects with a shared color

**Decision.** One profile assigns the same color to two disconnected components.

**Reason.** Otherwise a solver can group all cells by color rather than identify
4-connected components.  That shortcut fits the canonical pairs because their
object colors are distinct.

**Alternative rejected.** Merely randomizing the three colors still leaves the
same shortcut valid whenever all colors are unique.

**Failure mode controlled.** The shared-color witness makes `group_by_color`
disagree with the authority and is guaranteed once per five-profile schedule.

## D8: Build a source-bound 100-lessons-per-band probe

**Decision.** Add `workspace/lesson_probe.py`, using hashed seeds, non-overlapping
index ranges, actual generator declarations, and every cyclic schedule start.

**Reason.** The battery's 12-lesson semantic sample is a smoke test.  A cheap
1,800-draw Python probe gives stronger evidence about complete lesson windows
without model inference.

**Alternatives rejected.** Sampling individual witnesses cannot establish that a
whole lesson refutes each surviving rival.  Hard-coding competitor names in the
tool would drift from source.

**Failure mode controlled.** The report binds itself to the generator SHA and
records unique-input counts, rival disagreements, strict support, schedule
policy, and limitations.  Racket is not called 1,800 times; parity is delegated
to the independent rule-smoke gate.

## D9: Preserve failed iterations rather than smoothing the history

The initial before battery is retained as incomplete after an external
interruption.  The 11-test red run, missing-probe red run, lint identifier
failure, and 16.7% profile-floor failure are all retained.  None is presented as
a final failure, but each explains a concrete source change and prevents the
review from overstating first-pass success.
