# Working notes: aa0b08801e61

## 2026-10-23 mask-bank integrity repair

Final generator version: `4.0.1`

Final generator SHA-256: `502670fabf624ce35cf4e44cdc599c840806106602b5d85a4a727d950bb7a395`

Pinned canonical rule hash: `febf74c1fcfe` (unchanged)

### Defect and repair

The declared `_UD_CROWN` teaching mask was byte-for-byte identical to
`_UD_CANONICAL`. The source therefore claimed twelve masks and two novel masks
per symmetry class while actually providing only eleven unique masks and only
one novel up-down mask. A `mask_trap` draw could silently select the canonical
up-down mask, weakening the intended exact-mask-lookup counterexample coverage.

`_UD_CROWN` is now a distinct connected 3×3 mask with up-down symmetry only.
Import-time assertions now enforce the complete declaration contract: exactly
three masks per class, no within-bank or cross-bank duplicates, one canonical
first entry, two noncanonical teaching entries, connectedness, and the declared
symmetry class. The reusable `workspace/semantic_probe.py` now reports and fails
on mask-bank declaration drift, so later agents do not have to rediscover this
source-level invariant manually.

### Verification and retained evidence

- Protected task tests: 41 passed in
  `checks/task-tests-final-mask-bank-repair/result.json`; the two new regression tests
  first reproduced the 11/12 uniqueness defect before the source change.
- Source-bound semantic probe: 12 declared/12 unique masks, four canonical and
  eight novel; all four banks report 3/3 class matches and connected masks;
  294/294 joint overrides and 48/48 lesson rotations passed in
  `checks/semantic-probe-mask-bank-repair.json`.
- The deterministic shortcut counterexample was refreshed against generator
  hash `502670...a395`; Racket rule hash `febf74c1fcfe` still matches the
  catalog and differs from canonical-mask lookup on 13 cells.
- A bounded adversarial pass reached all eight novel masks within six
  `mask_trap` draws, checked four representative min/max override scenes, and
  found exact Python/Racket parity with valid generator domains in
  `checks/mask-bank-adversarial/verification.json`.

### Current decisions and limits

Keep the canonical Racket authority and the finite audited-bank/corner-placement
design unchanged; this repair restores the design's own declared diversity
rather than expanding its scope. The finite bank and corner-biased layout remain
visible sampler fingerprints, and the declared rival set is finite evidence,
not universal identifiability. No full production battery or large fresh census
was rerun because the changed surface was the mask declaration plus its local
contract; the protected staged tests, exhaustive declared-bank probe, exact
Racket counterexample, and bounded parity attack cover that surface directly.

## 2026-10-12 review outcome

Final generator version: `4.0.0`

Final generator SHA-256: `3649031665011fb6e1cfb9b7a1532efc12bc9cb4996555661e564e2410c7ade4`

Pinned canonical rule hash: `febf74c1fcfe`

The canonical Racket authority was not changed. Its rule classifies each
nonzero monochrome 4-connected object's tight mask by left-right and up-down
reflection symmetry: both symmetries → 8, left-right only → 2, up-down only →
3, neither → 4.

### Reproduced baseline defects

The issued `3.0.1` sampler had no `RULE_HASH`; advertised eight axes while most
were ignored or band-incompatible; accepted unknown controls; used capped
random placement; validated almost nothing; and declared no executable strict
profile, shortcut, witness, or lesson-identifiability contract. Its
`self_check` accepted every destructive native mutation (0/55 rejected).

The immutable before battery, source SHA
`ba55a98f80c66e1ba16defb6241ad023196ee97c165ca3c690e06f30a680ae24`,
finished with 6 green, 2 advisory, and 4 failed stages: lint, self-check,
defect lint, and exact overrides. See `checks/before/`.

### Final design

- The public contract is now only three real exact controls: `grid_h=9..15`,
  `grid_w=12..18`, and `n_objects=3..4`. Every joint tuple works in every
  difficulty band; unknown, out-of-range, bool, and non-integer controls fail
  loudly.
- Generation is constructive. Three or four connected masks are placed in
  separated corners with distinct source colors and distinct symmetry classes;
  there is no retry-exhaustion fallback.
- Canonical profiles recur deterministically, while a period-four curriculum
  alternates canonical-mask examples with `mask_trap` examples made from novel
  masks of the same semantic symmetry classes.
- `self_check` validates dimensions, colors, component count, distinct colors,
  4-connectivity, 3×3 mask membership, distinct classes, one-cell including-
  diagonal separation, and exact override realization.
- `strict_canonical_like`, `rule_mirror`, one canonical-fitting shortcut,
  one witness, and `lesson_identifiable` make the semantic contract executable.
- `workspace/semantic_probe.py` is a reusable source-bound authoring tool. It
  enumerates all 294 band×joint-axis requests, all declared schedule starts and
  query rotations, all declared canonical shortcuts, profile support, and one
  exact generated shortcut counterexample.

### Strongest known shortcut and retained counterexample

The strongest plausible shortcut is exact canonical-mask lookup: memorize the
four masks in the public task and map any unknown mask to color 4. It fits all
4/4 canonical pairs. The final generator deliberately emits novel masks that
share the intended symmetry class but are absent from that lookup.

At seed `20261012`, sample index `1`, difficulty `medium`, profile `mask_trap`,
a novel 2×2 square is both left-right and up-down symmetric. The Racket rule
colors it 8; the shortcut colors it 4. The full input, outputs, four differing
cells, hashes, and authority receipt are retained in
`counterexamples/canonical-mask-lookup/counterexample.json` and
`checks/counterexample-aa0b08801e61/racket.json`.

### Final evidence

- Native after battery: 12/12 green, zero advisories, under `checks/after/`.
- Exact override gate: 8,640/8,640 draws accepted with zero findings across 96
  cases and all three bands.
- Native semantic census: 600 draws, 297 strict canonical-like (49.5%, declared
  floor 35%), all canonical inputs accepted, declared witness present.
- Profile floor: 49/60 exact canonical-profile hits; easy 18/20, medium 15/20,
  hard 16/20.
- Protected task tests: 39 passed under `checks/task-tests-final2/`.
- Task-local semantic probe: 294/294 joint overrides exact and lawful; 12/12
  ordered lessons and 48/48 query rotations identifiable.
- Production lesson census: 300/300 lessons materialized, 1,200 unique inputs,
  0 production ambiguities, and 0/1,200 ambiguous held-out rotations. The
  canonical-mask rival was refuted in every lesson in each band.
- Declared-period census at fixed seed 0: all 12 start/band lessons and all 48
  query rotations identifiable.
- Final exposed visible-only solve: one revision, all 3 visible demonstrations
  passed; earlier rule exposure declared `yes`, reference consulted `no`, and
  solve bound to the final generator hash.

### Decisions and limits

The earlier free-form random-shape design was replaced rather than patched
because its broad stated API was not observable and its validator could not
protect the rule domain. The new design intentionally narrows production to a
small audited shape bank and corner-biased layout. This creates a visible
sampler fingerprint, but it keeps canonical morphology, exact controls, and the
known shortcut distinction auditable; expanding the bank is the preferred
future improvement.

The declared-rival checks are finite evidence, not proof of universal
identifiability. The probe's Python mirror is diagnostic only; retained labels
and the counterexample were checked against the selected Racket authority.
Future changes to masks, lesson assembly, query policy, or duplicate handling
must rerun the full battery, protected tests, 300-per-band production census,
and declared-period rotation census.
## Current reviewer considerations

Source SHA-256: `502670fabf624ce35cf4e44cdc599c840806106602b5d85a4a727d950bb7a395`.

# Decisions — aa0b08801e61

## D1 — Keep the canonical Racket authority unchanged

**Prior choice.** The packet supplied the canonical symmetry-class rule but the
generator did not pin it. The original rationale for omitting `RULE_HASH` is
unknown; no useful task note explained it.

**Decision.** Keep the Racket program unchanged and pin
`RULE_HASH = "febf74c1fcfe"`.

**Rationale.** All four canonical pairs, native rule smoke, authority sync, and
Racket checks agree on the same rule. The reproduced defects were in sampling,
validation, exact controls, and teaching evidence—not label authority.

**Rejected alternative.** Rewriting the rule would create a needless authority
change and confound distribution repair with semantics.

**Evidence.** `checks/after/checks/aa0b08801e61_after_rule_smoke.json`,
`checks/after/checks/aa0b08801e61_after_authority_sync.json`, and
`checks/counterexample-aa0b08801e61/racket.json`.

## D2 — Replace capped random packing with constructive placement

**Prior choice.** Version 3.0.1 tried up to 50 scenes and 40 placements per
shape, then returned the last grid even after failure. It marked whole bounding
boxes occupied while painting only mask cells. The historical rationale appears
to have been shape diversity, but exact failure behavior was undocumented.

**Decision.** Select masks first and place at most four of them in separated
corners. Validate the constructed grid before returning it.

**Rationale.** The minimum 9×12 grid easily accommodates four 3×3 masks with
one-cell including-diagonal separation. A constructive algorithm makes success
total for every legal exact request and removes silent partial fallback.

**Rejected alternatives.** More retries still leave probabilistic failure.
Post-hoc rejection/resampling hides cost and can distort lesson schedules.
Tracking only bounding boxes unnecessarily constrains actual occupied pixels.

**Failure modes/limits.** Corner placement is visibly biased. It is accepted as
auditability over maximal spatial diversity; future expansion should add a
constructive interior-slot planner, not restore retries.

**Evidence.** Native self-check, defect lint, 8,640-draw override gate, and the
294-case task-local joint enumeration.

## D3 — Advertise only exact controls that really exist

**Prior choice.** The baseline declared `grid_h`, `grid_w`, `palette_kind`,
`n_blobs`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and
`texture`, although most were ignored, some were aliases or singleton labels,
and dimensions/counts were band-dependent. Unknown keys were not rejected.
Original rationale beyond generic “combinatorial axes” is unknown.

**Decision.** Keep only `grid_h=9..15`, `grid_w=12..18`, and
`n_objects=3..4`; make all three exact, observable, and legal in every band.
Reject unknown keys, bools, non-integers, and out-of-range values.

**Rationale.** A small truthful API is more useful than an expansive inert one.
Difficulty now affects deterministic defaults only, never legality.

**Rejected alternatives.** Keeping decorative axes as “diagnostic” would still
invite consumers to treat them as controls. Keeping the old 8..18/9..20/3..6
domain would require a more complex placement system and drift farther from all
four canonical profiles without adding a semantic distinction.

**Evidence.** `checks/after/checks/aa0b08801e61_after_override.log` and
`checks/semantic-probe.json`.

## D4 — Use a small audited mask bank with distinct classes per scene

**Prior choice.** The baseline procedurally synthesized rectangles, pluses,
T-like shapes, and random asymmetric blobs. It could repeat symmetry classes,
reuse source colors, and its `self_check` did not inspect components or masks.

**Decision.** Declare three connected masks for each of the four symmetry
classes: one canonical mask plus two novel masks. A scene has three or four
objects, each with a distinct source color and a distinct class.

**Rationale.** Every mask can be reviewed at source, import-time assertions
verify its class/connectivity, and each scene gives multiple class contrasts.
The bank includes a canonical profile and direct counterexamples to exact-mask
memorization.

**Rejected alternatives.** Unbounded procedural random blobs increase shape
variety but make semantic coverage and validator completeness harder to prove.
Using only the four canonical masks would preserve morphology but teach the
strongest wrong shortcut perfectly.

**Failure modes/limits.** The finite bank itself is a distribution fingerprint.
The next safe extension is to add independently reviewed masks and rerun the
semantic probe/censuses; it is not evidence that arbitrary connected shapes are
covered.

## D5 — Schedule canonical support and shortcut-breaking examples explicitly

**Prior choice.** Baseline examples were independent random draws with no lesson
schedule or executable identifiability contract.

**Decision.** Declare period four:
`canonical_lr`, `mask_trap`, `canonical_ud`, `mask_trap`. Each lesson has three
demonstrations. Every consecutive schedule start and every one-of-four held-out
query position must contain a `mask_trap` demonstration that refutes
`canonical_mask_lookup`.

**Rationale.** Correct individual labels do not guarantee that demonstrations
identify the rule. The deterministic schedule makes the relevant distinction a
lesson-level invariant rather than a frequency hope.

**Rejected alternatives.** Randomly sampling novel masks could still produce an
all-canonical lesson. A canonical-only schedule cannot distinguish semantic
symmetry from exact mask lookup. An ordered-only contract would fail downstream
assemblers that rotate the query.

**Evidence.** `checks/lesson-census.summary.json` (300 lessons, 1,200 rotations),
`checks/schedule-census.summary.json` (all declared starts at fixed seed 0), and
`checks/semantic-probe.json` (12 starts/bands, 48 rotations).

## D6 — Make the validator describe the actual sampled manifold

**Prior choice.** Baseline `self_check` returned success for empty/all-background,
tiny, repeated-color, malformed-domain, and destructive mutations; native
self-check rejected 0/55 mutations.

**Decision.** Validate rectangular integer ARC grids, exact dimension domain,
three/four components, distinct colors, 3..9 cells, ≤3×3 tight boxes,
4-connectivity, declared masks, distinct symmetry classes, including-diagonal
padding, and any supplied exact override metadata.

**Rationale.** The validator should reject inputs that violate assumptions used
by the generator and semantic tools, not merely check for nonzero pixels.

**Rejected alternative.** A broad “rule domain” validator accepting arbitrary
shapes would be useful for authority reasoning but would not catch sampler
drift. The independent rule mirror and canonical checks cover that broader
semantic layer.

**Limit.** `self_check` intentionally validates the production manifold rather
than every lawful Racket input; canonical inputs are explicitly required and
all four pass.

## D7 — Encode the strongest plausible rival as executable evidence

**Decision.** Declare `canonical_mask_lookup` in
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; add a witness
predicate and `lesson_identifiable`.

**Rationale.** The four canonical examples use four fixed masks, making exact
lookup a simpler plausible hypothesis. The retained 2×2-square case proves why
novel masks are necessary: Racket outputs 8 while lookup outputs 4.

**Rejected alternatives.** Identity, source-color mapping, or object-order rules
are weaker because canonical pairs already refute them. Prose-only warnings
cannot be checked by lesson tooling.

**Evidence.** `QUESTION_ANSWER.md`,
`repo/generators/aa0b08801e61/counterexamples/canonical-mask-lookup/counterexample.json`,
and `checks/counterexample-aa0b08801e61/racket.json`.

## D8 — Add a reusable source-bound semantic probe

**Decision.** Add `workspace/semantic_probe.py` and two portable regressions.

**Rationale.** Future agents should not have to reconstruct exact-axis Cartesian
coverage, declared-period rotations, shortcut fit, profile support, or the
counterexample from review prose. The tool reads the selected module and its
actual declarations through `reviewer_support`, then emits a JSON report.

**Probe coverage.** 294 band×joint-axis calls; 98 unique exact triples; 12
ordered lessons; 48 rotations; 4 canonical pairs; 60 default support draws; one
retained witness.

**Limit.** It uses the Python mirror for fast authoring diagnostics. Racket
authority is checked separately and preserved in the retained counterexample.

## D9 — Retain canonical profile weight while keeping full axis support

**Decision.** Seven of every eight default indices choose one of four canonical
size/count profiles; the eighth cycles through the entire axis domain. The
schedule independently chooses canonical or novel masks.

**Rationale.** The baseline profile floor had weak/zero band support. This split
produces deterministic canonical morphology without making noncanonical exact
requests unreachable.

**Rejected alternatives.** Always canonical dimensions would make portions of
the public axes dead. Uniform dimensions would make exact canonical-profile
support too sparse and unstable under a 20-draw band census.

**Evidence.** Native profile floor: easy 18/20, medium 15/20, hard 16/20, 49/60
pooled. Task-local deterministic sample: 10/20 strict canonical-like in each
band with 20/20 unique inputs.

## D10 — Stop after final-source replay and document the remaining fingerprint

**Decision.** Do not add more axes, random decorations, or undeclared rivals
once the final generator passes all native gates, protected tests, authority
counterexample, production census, and exhaustive declared-period census.

**Rationale.** Additional complexity would increase failure surface and sampler
fingerprints without a reproduced defect. The final source hash is shared by the
battery, solve, census, probe, and Racket receipt.

**Remaining uncertainty.** A learner may discover shortcuts outside the finite
rival set, and the small mask bank/corner layout is recognizable. These are
explicit limits, not claimed solved problems.

# Decisions — review-577f265ee64db743

## Native family scope

The production generator and canonical authority remain unchanged.  This review
adds a task-local native family under `workspace/parametric/` with two
matched-input settings:

- `classify_all` is the byte-exact canonical default and symmetry-classifies
  every nonzero monochrome four-connected object.
- `signal_rank` counts the unique blue signal, uses that count as a one-based
  rank among non-blue objects in row-major component order, and
  symmetry-classifies only the selected object.

The adapter supports 2–6 demonstrations and 1–4 independently requested,
prefix-stable queries.  Its fourth query is a substantive 30×30 scene; inputs
are setting-independent and the first two demonstrations use different ranks
and selected symmetry classes.

## Teaching and verification decision

The lesson bank explicitly checks twelve plausible shortcuts, including fixed,
reversed, column-major, size-based, color-based and source-color rules.  A
64-seed finite audit covered 384 episodes, 2,944 labeled pairs and 384 exact
30×30 query pairs with no surviving declared rival.  This is finite evidence,
not universal uniqueness.

The staged task suite passed 60 tests.  Native qualification covered both
settings at seeds 0 and 17 with three demonstrations and four queries: four
jobs, 28 retained labels and 40 protected-Racket evaluations.  The protected
causal witness replaces the measured rank 5 with rank 1 on the same qualified
input; it selects a different object and changes the final grid.  Sixteen
single-query public projections passed source binding, masking, visible-byte
identity, schema and duplicate checks.

Exact bindings are retained in `checks/aa0b08801e61/`.  The source/evidence
manifest SHA-256 is
`0a7cf95de112bba02a643dd962d849702fa9e65111d9f09d02cfa4ba86172ea7`;
qualification execution SHA-256 is
`7f7750b25fb72eb23fccd4d6823358c20d9369b0a077c752fb4a6c4487c095df`;
the witness SHA-256 is
`4d76b4217b667c29e1441ee1f2c36aaa5b578b93340aa962f85d4901a3786c74`.

## Handoff limit

Status is reviewer-ready and owner-pending.  Exact-byte owner integration,
fresh native qualification, witness replay, acceptance and explicit training
admission remain required.
