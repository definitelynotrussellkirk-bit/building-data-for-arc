# Working notes: 1a5d49e539de

## Parametric extension (assignment `review-ad11f5c06ca73080`)

- **Decision:** retain the approved left-right rule as the canonical/default
  setting and add only a task-local, unapproved `symmetry_axis=top-bottom`
  prototype. The selected generator remains byte-identical at
  `cc9524450ef524c7685a084aba5bd9dbba9455934a30af32d55ed62554312d37`;
  no production, canonical, approval, or training-admission state changed.
- **Episode contract:** choose one axis from the seed, fix it across three
  demonstrations and four distinct queries, label through the matching exact
  Racket program, and retain a scene only when the alternative axis predicts a
  different crop. Public output is an allowlist of demonstrations and masked
  query inputs; private settings, seeds, programs, and query answers do not
  affect the visible-content identifier.
- **Sampler ruling:** a `+12` retry preserved both the size-role and target-slot
  congruences and could trap a query where both axis rules always selected the
  same object. The final `+3` retry preserves the mod-3 size role but varies the
  mod-4 target position; disjoint bounded intervals prevent cross-pair reuse.
- **Retained artifacts:** `workspace/parametric/prototype.py`, both exact Racket
  programs, two public examples, eight focused tests, and
  `workspace/parametric/adversarial_probe.py` for future reviewers.
- **Evidence:** `checks/parametric/symmetry-axis-final/` records two settings,
  3+4 pairs each and 28 Racket evaluations; `task-tests-final/` is 41/41 green;
  `adversarial-final/` covers 24 episode configurations / 168 pairs with at most
  one retry and exercises count, numeric, projection, labeler and exhaustion
  rejection paths.
- **Supplementary tickets:** the retained tool diagnostics were reproduced but
  are already repaired in their current source, so the proposed disposition is
  close-as-accepted-feedback/no-change. The peer witness confirms a lawful
  `ignore_singletons` counterexample with ten differing cells and exact Racket
  parity; it is positive coverage, not a safety finding.
- **Next action:** a maintainer may review the proposed axis as a separate
  variant. Promotion would still require an explicit API/training decision and
  broader support than the two retained settings/seeds; this package does not
  make that decision.

## Review repair (assignment `review-2eb149c328bf615a`)

### Baseline evidence

The imported v2.0.1 source had SHA-256
`1cafc4a25be203ba53a2f65638a97e427e8451db0b878102a4923f44dbf9c44d`.
The immutable baseline probes established all of the following:

- generated maximum object size was 14 while the canonical median maximum was
  20 (`checks/before-defect/`);
- `self_check` accepted blank/full, singleton, short-line and solid-2x2
  impostors and rejected only 6/49 destructive mutations;
- four advertised helpful textures were byte-identical to the default path,
  ordinary and degenerate texture domains overlapped, unknown keys were
  accepted, and the override matrix produced thousands of findings;
- exact canonical profile support was 0/60 and there was no semantic contract;
- the target alone used a varied colour while all decoys used colour 2, so a
  `unique_component_color` selector solved generated scenes even though the
  canonical pairs use one shared object colour;
- active selected Racket text differed from canonical text, although sampled
  execution was equivalent.

### Canonical facts used for the repair

After de-duplicating imported aliases, the public task has four distinct pairs.
Every input is a 20, 21, 22 or 23 square with one nonzero colour and exactly four
8-connected objects. Three objects are left-right symmetric and one is not.
Canonical objects contain diagonal joins: the four objects decompose into 8,
9, 13 or 10 four-connected fragments depending on the pair. The target is not
fixed by scan index, colour, size or horizontal position.

### Selected design

- Preserve the pinned rule `71d6cfb99295`: scan same-colour 8-connected
  objects in row-major discovery order and crop the first left-right-asymmetric
  object.
- Generate exactly four separated same-colour objects in canonical-scale square
  grids. Three are verified symmetric decoys; one is verified asymmetric.
- Construct 8-connected shapes with ten total four-connected fragments per
  scene, covering canonical diagonal-join morphology rather than producing four
  ordinary 4-connected blobs.
- Cycle target size roles `smallest`, `second-smallest`, `largest` every three
  samples and target quadrant every four samples. Three demonstrations refute
  every declared selector; all four query rotations remain identifiable.
- Retire unverifiable legacy controls. Expose only exact integer axes
  `grid_size=20..23` and `color=1..9`; reject unknown keys, booleans, invalid
  values and invalid difficulty names.
- Make `self_check` enforce the full teaching domain: square size, ARC integer
  cells, one shared foreground colour, exactly four nontrivial/non-solid
  8-connected objects, exactly 3/1 symmetry split, and 8..13 four-connected
  fragments.
- Declare executable rivals for first/last, smallest/second-smallest/largest,
  leftmost/rightmost, and unique component colour. The lesson hook validates
  labels and rejects only shortcuts that fit all demonstrations but change the
  query. Schedule coverage is measured separately rather than imposed as a
  brittle per-rotation checklist.
- Keep an independent Python rule mirror for tests and probes; Racket remains
  output authority.

### Test-first evidence

- `checks/red-task-tests/`: 29 failures / 1 pass before the main repair.
- `checks/red-fragment-tests/`: 3 failures / 27 passes after the first repair,
  exposing missing canonical diagonal morphology.
- `checks/red-rotation-hook/`: 3 failures / 30 passes, reproducing the
  over-constrained query-rotation warning.
- `checks/task-tests-final/`: 33/33 pass on final source.

The final generator SHA-256 is
`cc9524450ef524c7685a084aba5bd9dbba9455934a30af32d55ed62554312d37`.

### Final measurements

- Full after battery: 12/12 green, zero advisory or failed stages
  (`checks/after-final/`).
- Racket smoke: 120/120 applications fired, 120/120 mirror matches, no crashes,
  mutations or out-of-bounds outputs.
- Canonical profile: 8/8 imported canonical inputs accepted; exact profile
  60/60 across three bands.
- Semantic gate: 600/600 strict-domain draws, all eight witnesses fired, all
  declared rival claims verified, 12/12 sampled lessons identifiable, and
  0/48 diagnostic query rotations ambiguous.
- Production lesson census: 300/300 lessons, 1,200 unique inputs, zero lesson or
  query-rotation ambiguities and zero hook warnings.
- Override gate: 50 cases x 30 seeds x 3 bands = 4,500 accepted draws, zero
  findings or warnings; unknown keys rejected.
- Retained probe: 100 draws and 100 lesson windows per band, all inputs and
  outputs unique within band, target indices exactly 25 each, target size ranks
  34/33/33 for ranks 0/1/3, and 144 exact axis-corner cases with zero failures.

### Racket authority

The selected `target_code` fields in the training and augmented records were
synchronized byte-for-byte to the canonical program solution. This changes no
rule behavior and preserves rule hash `71d6cfb99295`. The two archival
`raw_code` fields remain textually different but solve all canonical pairs;
final execution parity passes over both distinct source texts.

### Limits

This is finite evidence against the declared shortcut family, not a proof
against every possible hypothesis or a model-accuracy claim. The grammar is
intentionally narrow: one foreground colour, exactly four separated objects,
20--23 square boards, and exactly one asymmetric object. The generator produces
one representative canonical diagonal-fragment count (10) while the validator
accepts the observed canonical range 8..13.
## Current reviewer considerations

Source SHA-256: `cc9524450ef524c7685a084aba5bd9dbba9455934a30af32d55ed62554312d37`.

# Decisions — `1a5d49e539de`

## D1 — Preserve the canonical rule

**Input choice.** Treat equal-coloured nonzero cells as 8-connected objects,
scan them in row-major discovery order and return the tight crop of the first
object that is not symmetric under left-right reflection.

**Rationale.** This is the pinned canonical behavior (`71d6cfb99295`) and solves
all public pairs. The review found a data-distribution defect, not a rule defect.

**Alternatives considered.** Select the unique asymmetric object independent of
scan order; use 4-connectivity; infer a colour-specific target. The first is
extensionally equivalent only while uniqueness holds, the second splits
canonical diagonal joins, and the third is the exact shortcut being removed.

**Probe/failure mode.** Racket smoke and independent Python-oracle tests cover
all generated draws; malformed scenes with zero or multiple asymmetric objects
are rejected. The retained limitation is that uniqueness remains part of the
teaching grammar.

## D2 — Use four same-colour objects on canonical-size square boards

**Input choice.** Exactly four separated objects, one shared nonzero colour, and
side length 20--23.

**Original rationale.** Unknown; v2.0.1 used smaller, variable scenes and a
special target colour. Baseline evidence showed canonical maximum object scale
was unreachable and unique colour leaked the answer.

**Alternatives considered.** Keep smaller boards and only enlarge objects;
retain mixed colours but balance them; replay exact canonical grids. Smaller
boards still miss the public joint profile, balanced mixed colours add an
unsupported task factor, and exact replay provides little diversity.

**Probe/failure mode.** Profile floor is 60/60 exact and the lesson census finds
no surviving unique-colour rival. The narrow square/one-colour domain is
intentional and documented.

## D3 — Match both 8-connected objects and 4-connected fragment morphology

**Input choice.** Construct four 8-connected objects containing ten total
4-connected fragments; accept the canonical 8..13 range in `self_check`.

**Rationale.** Canonical shapes connect many subparts diagonally. The first
repair matched the semantic object count but produced four ordinary
4-connected blobs, a detectable distribution shift.

**Alternatives considered.** Ignore the fragment statistic because the rule uses
8-connectivity; sample the exact canonical count distribution; hard-code
canonical shapes. Ignoring it loses visible morphology, exact-distribution
sampling adds complexity without known value, and hard-coding harms diversity.
Ten is a representative canonical value while 8..13 keeps all public examples
lawful.

**Probe/failure mode.** `checks/red-fragment-tests/` proves the regression;
final defect lint flags zero. The generator does not yet sample every count in
the accepted range.

## D4 — Cross size role and position deterministically

**Input choice.** Target size role cycles smallest / second-smallest / largest
modulo 3; target quadrant cycles modulo 4.

**Rationale.** Three demonstrations then refute fixed size selectors, while
sliding windows move the target through every scan position and horizontal
side. A deterministic schedule is easier to audit than probabilistic witness
coverage.

**Alternatives considered.** Random roles; four-example schedule with one role
per rank; always canonical scan positions. Random roles can produce ambiguous
lessons, four required demonstrations cost more data, and fixed positions teach
scan-order shortcuts.

**Probe/failure mode.** The final probe measures ranks 34/33/33 and positions
25 each per 100 draws; every declared rival is refuted in all 100 windows per
band. Overlapping mod-3/mod-4 cycles repeat every 12 samples, so the probe tests
cyclic starts and query rotations.

## D5 — Expose only truthful, exact controls

**Input choice.** Keep `grid_size` (20..23) and `color` (1..9); remove all legacy
textures, anchor/asymmetry flags, palette aliases and fake dimensions.

**Rationale.** The old surface advertised behavior it did not provide and made
the override matrix largely meaningless. Two observable axes cover useful
variation without hidden incompatibilities.

**Alternatives considered.** Repair every old axis; mark them diagnostic; keep
textures as aliases. Most had no canonical justification, and aliases create
multiple names for the same observable. YAGNI favored retirement.

**Probe/failure mode.** The battery exercises 4,500 requests and the retained
probe exhausts 144 band/size/colour corners. Unknown keys and invalid types are
explicitly rejected. This is a deliberate compatibility break from v2.0.1.

## D6 — Make validation describe the actual legal domain

**Input choice.** Validate dimensions, rectangularity, integer ARC colours,
one foreground colour, four 8-connected objects, nontrivial/non-solid shapes,
3/1 symmetry split and 8..13 four-connected fragments.

**Rationale.** A validator that accepts trivial impostors cannot protect
training data or support meaningful mutation tests.

**Alternatives considered.** Minimal “one asymmetric object” validation; exact
generator-template validation. The first remains toothless; the second would
reject lawful canonical variants and overfit implementation details.

**Probe/failure mode.** Mutation and explicit-impostor tests cover blank/full,
singleton, line, solid block, missing/extra object, recolour, symmetry and
fragment failures. The validator intentionally rejects scenes outside the
reviewed grammar even if the canonical Racket program returns some output.

## D7 — Declare executable shortcut rules and witnesses

**Input choice.** Rivals are first, last, smallest, second-smallest, largest,
leftmost, rightmost and unique component colour; witnesses are executable
predicates tied to those rivals.

**Rationale.** The baseline defect was lesson-level: labels were correct but a
wrong rule explained the demonstrations. Executable rivals turn “should be
varied” into a falsifiable claim.

**Alternatives considered.** Descriptive witness names only; model-based
solving; exhaustive program search. Names without code cannot be verified,
model inference is expensive and unstable, and exhaustive synthesis is not
cheap enough for every generator check.

**Probe/failure mode.** The semantic gate verifies all claims and the production
census checks complete lessons and rotations. The finite bank can miss an
unanticipated shortcut, motivating feedback F1.

## D8 — Define lesson identifiability extensionally

**Input choice.** Reject a lesson only when a declared competitor matches every
demo and changes the query, after validating labels and domain membership.
Measure schedule-profile coverage separately.

**Rationale.** An earlier hook required demo ranks `{0,1,3}` even on rotated
queries. The census showed 0 rival ambiguity but 600 warnings because removing
one pair can leave only two rank classes. The checklist was stricter than the
actual identifiability condition.

**Alternatives considered.** Keep warnings; redesign four pairs so every
three-subset covers three roles; disable rotations. The first creates false
alarms, the second is combinatorially impossible with only three repeated roles
for every subset, and the third hides query-position fragility.

**Probe/failure mode.** `checks/red-rotation-hook/` fails before the change;
final census has zero warnings and 0/1,200 ambiguous rotations.

## D9 — Keep an independent mirror, but retain Racket authority

**Input choice.** Implement a small Python mirror for tests/rivals while all
source-bound labels and parity claims come from the pinned Racket rule.

**Rationale.** A mirror makes fast local property tests possible; independent
Racket comparison prevents shared Python mistakes from becoming authority.

**Alternatives considered.** Racket-only tests; Python as authority. Racket-only
would make 4,500+ probes expensive, while Python authority violates the packet
contract.

**Probe/failure mode.** Final smoke checks 120/120 mirror matches. Any future
Racket hash change should invalidate the pin and require re-review.

## D10 — Synchronize active authority text, preserve archival source

**Input choice.** Replace only the selected `target_code` fields with the exact
canonical program; do not rewrite `raw_code`.

**Rationale.** Active authorities should have one exact source. The archival
text is useful provenance and already executes equivalently.

**Alternatives considered.** Leave active beautification; rewrite every field;
change the canonical program. Leaving it fails authority sync, rewriting raw
history destroys provenance, and changing canonical authority is unnecessary.

**Probe/failure mode.** Authority sync reports one selected exact group and PASS
execution parity over two total source texts. This is R4, a textual
synchronization rather than a semantic rule change.

## D11 — Retain tests and a future-agent probe

**Input choice.** Add 33 focused tests and `workspace/review_probe.py` bound to
live rival declarations and source hash.

**Rationale.** Future edits need a cheap way to reproduce distribution,
override and lesson claims without rebuilding this review narrative.

**Alternatives considered.** Rely only on the global battery; copy rival names
into a standalone script. The battery does not expose every curriculum count,
and copied names silently go stale.

**Probe/failure mode.** The probe imports `LESSON_COMPETITORS`, tests 100 windows
per band and all axis corners, and writes a machine-readable receipt. It must be
run through `run_with_racket.py` (or with the documented `PYTHONPATH`).

## D12 — Do not edit audit targets

**Input choice.** Report `d48ec0001283` clean within measured scope and retain a
hash-bound counterexample for `bdcb4c9eb6bd` without patching either.

**Rationale.** The assignment explicitly separates audits from the assigned
repair. Editing them would broaden the patch and invalidate their assigned
hashes.

**Probe/failure mode.** Both full batteries and the supported Racket apply
receipt are packaged. `bdcb4c9eb6bd` remains unsafe until a separate owner fixes
its canonical validator, profile support, semantic/override contracts and
active authority drift.
