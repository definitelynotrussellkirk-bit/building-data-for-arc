# Working notes: 07eaf5f238ad

## Current rule and authority

The nonzero cells of row 0 form an ordered header. For each header color, the
selected Racket rule chooses the first same-color four-connected component in
the body (rows 1 onward), crops that component's bounding box, and packs the
crops left-to-right with one zero column between pieces. A missing header color
is skipped, a repeated header token repeats the same crop, and body objects
whose colors are absent from the header are ignored.

The canonical Racket authority was not changed. Generator version 3.0.0 pins
`RULE_HASH = d10bfd060d8f`. Final generator SHA-256:
`e086b388c06062a5a20b5f9164ad1e659b2892e8b85b89c5c88d1ed4c08edac6`.

## 2026-10-07 repair

The imported 2.0.1 source had no rule hash or semantic contract. Its declared
axes did not match its difficulty-specific draw bounds, unknown overrides were
silently accepted, `empty_header` overlapped ordinary and negative texture
domains, `self_check` accepted one-color impostors, and no sampled output hit an
exact canonical `(height,width,palette-size)` profile. The baseline battery was
7 green, 2 advisory, and 3 failed.

Version 3.0.0 makes the control surface exact and observable:

- `grid_h=8..16`, `grid_w=10..18`, `n_header=2..4`;
- lawful textures `plain`, `absent_color`, `repeat_header`, `first_wins`,
  `decoy_colors`, and `rich`;
- unknown axes, wrong types, out-of-range integers, illegal textures, and
  unsupported difficulties fail loudly;
- `observe_overrides` recovers every advertised value from returned pixels.

The six-step schedule alternates rich semantic witnesses at even sample indexes
with exact canonical-profile anchors at odd indexes. In six consecutive starts,
the anchors cover 8x10/palette 3, 11x11/palette 4, and 11x12/palette 4. Every
four-example lesson contains at least one rich case. A rich case jointly shows
header order, a missing color, a repeated header token, first-vs-last object
selection, and an ignored non-header decoy.

`self_check` now validates dimensions, header grammar, the blank separator,
component size/bounds/halo separation, feature counts, texture classification,
packed-output bounds, and requested-vs-observed override values. Canonical
inputs remain accepted. The independent Python mirror matches the selected
Racket rule on canonical and generated cases.

Declared competitors are `body_scan_order`, `deduplicate_header`,
`last_object_of_color`, `require_all_header_colors`, and
`append_non_header_objects`. The last four fit all three canonical labeled
pairs; rich lessons refute all five. `lesson_identifiable` checks both labels
and competitor survival. The retained minimal repeated-header witness is
`counterexamples/deduplicate_header.json` and is covered by the focused tests.

## Final evidence

- Focused task tests: 12/12 pass (`checks/task-tests-final/`).
- Source-bound after battery: 12/12 stages green, with rotations required
  (`checks/after-5/`).
- Rule smoke: 120/120 applications, 120/120 Python-mirror parity, no mutation,
  crash, state, or bounds failure.
- Exact override matrix: 26,190/26,190 accepted draws, 291 cases, 0 findings.
- Profile floor: 26/60 exact canonical-profile hits; easy 7, medium 8, hard 11.
- Semantic census: 600/600 strict; 12/12 smoke lessons identifiable and 60/60
  smoke query rotations unambiguous.
- Wide lesson census: 300 production lessons (100 per band), four demos plus one
  query, 1,500 unique pairs and 1,500 query rotations, zero declared-rival
  ambiguity or scoring/materialization errors (`checks/lesson-census.json`).
- Fixed-seed schedule enumeration: all six residues in all three bands, 18/18
  lessons and 90/90 query rotations, zero ambiguity (`checks/schedule-census.json`).

## Assumptions and limits

The curriculum intentionally uses a small set of 2x2-bounded component shapes
and six halo-separated placement slots. This is enough to expose the selected
rule's branch distinctions, but it is not uniform coverage of every lawful
component shape or placement. The finite rival checks establish only that the
five declared alternatives are refuted on the measured lessons; they are not a
proof against every possible inferred rule. The Python mirror is verification
support, not label authority. Approval and training safety remain maintainer
catalog decisions.

No prior return was used as a repair lead; the task's retained notes were a
placeholder and associated-notes ledger was empty. The baseline source and
public checker evidence determined the repair.
## Current reviewer considerations

Source SHA-256: `e086b388c06062a5a20b5f9164ad1e659b2892e8b85b89c5c88d1ed4c08edac6`.

# Decisions for generator 07eaf5f238ad

## 1. Preserve the selected Racket authority

**Decision.** Do not edit canonical puzzle data or the selected Racket program.
Pin the generator to `RULE_HASH = d10bfd060d8f`, treat Racket as label authority,
and use an independently written Python mirror only for parity, rival scoring,
and fast task-local tests.

**Why.** The assignment was to repair the generator, not reinterpret the ARC
rule. The original failures were in the source distribution and its contracts.
Final rule-smoke and authority-sync evidence confirms the unchanged selected
program executes and agrees with the mirror on generated cases.

**Rejected alternative.** Updating canonical data or Racket to accommodate old
generator quirks would reverse the authority relationship and hide the actual
generator defects.

## 2. Replace implicit difficulty ranges with one honest public domain

**Decision.** Advertise `grid_h=8..16`, `grid_w=10..18`, and `n_header=2..4`, and
make exact overrides strict and observable at every difficulty. Difficulty may
choose defaults inside that domain but may not silently redefine the axis.

**Why.** The old declared ranges disagreed with its difficulty-conditioned draws,
so downstream enumeration could neither trust accepted values nor infer what a
returned grid realized. A single exact domain makes validation, override testing,
and curriculum assembly compositional.

**Rejected alternative.** Publishing separate undocumented ranges per difficulty
would preserve the mismatch and complicate exact override semantics. Clamping
invalid values was also rejected because it makes requested and realized values
diverge silently.

## 3. Remove the ordinary/negative texture overlap

**Decision.** Use six lawful ordinary textures only:
`plain`, `absent_color`, `repeat_header`, `first_wins`, `decoy_colors`, and
`rich`. Declare no degenerate ordinary texture.

**Why.** `empty_header` had occupied both helpful and degenerate domains, making
ordinary distribution claims self-contradictory. The selected rule can produce
`[[0]]` on malformed or empty-selection inputs, but such inputs do not teach the
intended branch structure and are unnecessary for this production generator.

**Rejected alternative.** Keeping `empty_header` behind a flag would preserve an
ambiguous public grammar and weaken the ordinary-output invariant. A separate
negative-test fixture would be appropriate if maintainers later need malformed
input coverage.

## 4. Make each texture pixel-observable

**Decision.** Define textures through independent structural facts recoverable
from the returned grid:

- `plain`: all unique header colours present exactly once, no decoy;
- `absent_color`: exactly one distinct requested colour absent;
- `repeat_header`: exactly one header colour repeated once;
- `first_wins`: exactly one header colour has two body objects;
- `decoy_colors`: exactly one non-header object;
- `rich`: exactly one of each distinction together.

Implement `observe_overrides` from those facts and compare it with requested
values in `self_check`.

**Why.** Metadata-only distinctions cannot be independently audited. Pixel-level
observability lets the override battery prove that every accepted request was
actually realized.

**Rejected alternative.** Returning generation metadata alongside grids would
not help consumers that receive only ARC pixels and would allow the pixels and
claims to drift.

## 5. Alternate semantic witnesses with canonical-profile anchors

**Decision.** Use a six-step deterministic role schedule: even indexes are rich
semantic witnesses; odd indexes rotate through exact canonical profiles
8×10 with two distinct header colours, 11×11 with three, and 11×12 with three.
The resulting input palettes include background, so the measured palette sizes
are 3, 4, and 4.

**Why.** The baseline had zero exact canonical-profile hits, while pure canonical
anchors alone would preserve the strongest shortcuts. Alternation provides both
profile fidelity and repeated semantic separation. Any four consecutive starts
contain a rich witness, and any six cover all three canonical profiles.

**Rejected alternatives.** Pure random sampling could miss rare distinctions in
a short lesson. Pure rich sampling would never demonstrate exact canonical
profiles. Pure canonical-profile sampling would leave repeated-header,
first-vs-last, missing-colour, and decoy behavior unobserved.

## 6. Use a composite rich case instead of one distinction per lesson

**Decision.** A rich input jointly includes:

1. header order different from body scan order;
2. one absent requested colour;
3. one repeated header token;
4. two differently shaped objects of the first requested colour;
5. one non-header decoy.

**Why.** Lessons use four demonstrations. A single composite witness refutes all
five named rivals while leaving room for profile anchors and variation. Joint
construction also ensures the distinctions are observed under interaction, not
only in isolated toy cases.

**Rejected alternative.** Assigning one example per rival would require five or
more demonstrations or allow some four-example windows to omit a distinction.
It also makes schedule identifiability more fragile under query rotation.

## 7. Declare executable rivals that really fit canonical data

**Decision.** Score these deterministic competitors:

- `body_scan_order`;
- `deduplicate_header`;
- `last_object_of_color`;
- `require_all_header_colors`;
- `append_non_header_objects`.

Retain the exact minimal `deduplicate_header` witness under
`counterexamples/deduplicate_header.json` and test it directly.

**Why.** Four of these alternatives fit all three canonical labeled pairs, and
the fifth captures a natural order shortcut that the repaired body layout makes
visible. Executable rivals turn “seems teachable” into a reproducible finite
claim and expose which demonstrations refute which hypothesis.

**Rejected alternative.** Text-only rival descriptions are not source-bound and
cannot participate in production or rotation census checks. Adding a large set
of speculative rivals without witnesses would dilute evidence and create
unstable contracts.

## 8. Require identifiability after holding out every pair

**Decision.** Assemble lessons as four ordered demonstrations plus one query,
then require the selected labels to be correct and each declared rival either be
refuted by the demonstrations or agree on the query. Run both production-order
and every-pair rotation censuses.

**Why.** An ordered lesson can pass merely because the only useful witness is
always left in training. Rotation checks detect that positional dependence. The
wide census measured 300 production lessons and 1,500 held-out query rotations
with no ambiguity against the declared rivals.

**Rejected alternative.** Treating the semantic battery's ordered result as
sufficient would overclaim arbitrary-query support. Conversely, claiming proof
against all hypotheses was rejected because the rival set is finite.

## 9. Strengthen `self_check`, but keep it a task grammar—not a new authority

**Decision.** Validate rectangular dimensions, colour range, blank separator,
header multiplicities, connected monochrome components, bounded component sizes
and boxes, halo separation, feature counts, texture classification, nonempty
bounded packed output, and exact overrides. Accept canonical inputs that satisfy
that grammar.

**Why.** The old check accepted structural impostors, so source-bound gates could
validate inputs outside the intended manifold. The new checks enforce the
constructive contract while still allowing hand-authored canonical cases and
counterexamples.

**Rejected alternatives.** Recomputing labels in `self_check` through the Racket
source would couple validation to the authority runtime and make generation
expensive. Restricting validation to grids produced by this exact constructor
would make canonical and minimized witnesses unusable.

## 10. Keep the constructive shape/placement vocabulary deliberately small

**Decision.** Use a small set of connected shapes and six 2×2 placement slots
that remain valid at the 8×10 lower boundary, with halo separation. Ensure the
first and second same-colour objects have different crops.

**Why.** The bounded repair prioritizes reliable semantic distinctions, exact
small-grid feasibility, and exhaustive override testing. The slot design avoids
rejection loops and makes every legal override deterministic and inexpensive.

**Known restriction.** This is not uniform coverage of every lawful component
shape or body location. A future diversity extension could add larger boxes and
more placements while preserving the same observable texture/rival contract.
That restriction is documented rather than hidden.

**Rejected alternative.** Free-form rejection sampling made lower-bound grids
fragile, complicated exact overrides, and risked unbounded or highly variable
checker cost.

## 11. Retain genuine failures and minimize only the final evidence surface

**Decision.** Keep the baseline battery, failed lint iteration, task-test red
history, final full battery, wide censuses, audit reproducers, and solve records.
Use the return builder's verified evidence bundle when member count exceeds the
limit.

**Why.** The maintainer should be able to replay the decisive claims and inspect
real repair history without reconstructing it from prose. Bundling preserves
hashes while staying below the 256-member and 25 MiB expanded-size limits.

**Rejected alternative.** Deleting all intermediate failures would erase the
root-cause trail. Shipping every redundant full directory as ordinary ZIP
members would violate the packet contract and slow routine intake.

## 12. Do not modify shared tooling inside the task patch

**Decision.** Record shared issues in `FEEDBACK_TO_CODEX.md`, led by the completed
battery's misleading live-lock fields, but keep the allowed source delta confined
to `repo/generators/07eaf5f238ad/`.

**Why.** The assignment contract permits only task-local changes. Shared-tool
fixes need independent review and could affect all generators.

**Rejected alternative.** Opportunistically patching the linter, battery runner,
or override reporter would make this return unpackageable and mix unrelated risk
with the generator repair.
