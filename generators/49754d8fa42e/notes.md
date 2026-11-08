# Working notes: 49754d8fa42e

## Native reviewer handoff: 2026-10-24 / `review-b8b2624384781d95`

This review adds `workspace/parametric/composition.py` behind a native adapter
and promotion contract. Production v3.3.0, the canonical authority, and the
legacy fixed-rotation prototype are preserved. The native default is the exact
canonical program. Its alternative `orientation=modal_components` selects the
unique nonzero modal color, retains that color's input mask, counts its
4-connected components, and rotates the selected gray glyph by `(count-1)%4`.
The mask is the input-dependent intermediate; a counterfactual that counts all
colors' components changes the final output while leaving glyph selection and
the rotation procedure intact.

### Current decisions and concrete repairs

- Use two histogram-matched topology contrasts, followed by an actually rotated
  example of the other T/L class. Queries use only demonstrated modal classes.
  Independent demo/query limits are 2..6 and 1..4, with default 3/4 and identical
  first-query prefixes across query counts. The fourth query is a substantive
  30×30 scene. These scenes extend the separate native grammar, not the
  unchanged production controls.
- Source review found a real 8×9 capacity failure at seed 87: a fixed minimum
  of 30 modal cells exceeded the sampler's area-conditioned maximum of 28.
  Preserve that lawful canvas and condition the lower bound on component count;
  retain the exact failing-seed regression. Do not silently skip the seed or
  remove the small canvas.
- An independent protected-Racket review found a semantic teaching hole in the
  first working version. At seed 17 with three demos, the secondary T/L class
  appeared only with one component, so a rule that rotated only the primary
  color fit every demo and failed two queries. The retained failure is
  `checks/49754d8fa42e/color-gated-before.json` in this return. Demonstrate four
  components for the secondary class and audit rotation gated on each T/L
  color. The earlier 21-rival pass and 62-test pass predate this repair and do
  not establish final-source validity.
- Reuse the existing glyph/canonical helpers instead of modifying the old
  fixed-turn API. Keep the adapter free of nested Racket audits. The example
  builder and qualification worker execute the claimed labels independently.
- The reusable finite audit must apply a rival's selected color to both glyph
  lookup and component counting. Merely comparing an unrotated legacy rival
  against a rotated answer could conceal the selector shortcut. Retain literal
  protected-Racket semantic fixtures for the rival implementations.
- Export only one current query to an actor. Hash names from exact visible
  bytes; keep future query inputs, answers, programs, settings, total count,
  and sequence IDs private. The full public batch is controller material.
  Existing destinations and duplicate visible payloads are rejected before
  publication. Builder metadata explicitly says owner acceptance is pending.

### Evidence and next owner action

The current return's `REVIEW.md` and `RESULTS.json` index final tests, protected
finite audit, public-export checks, native qualification/execution, and the
source-bound causal witness. The task-local `evidence/current/` and native
`evidence/manifest.json` retain the compact evidence used by that qualification.
Historical evidence below remains historical and is not a claim about this
native composition.

The reviewer handoff is a proposed native family, not owner acceptance or
training admission. After checked integration, the owner must qualify and
accept the exact source. Finite rival coverage does not prove uniqueness against
all programs, arbitrary lesson reassembly, universal seed correctness, or
measured training benefit. Preserve the production curriculum's existing
ordered-lesson limitation.

---

## Current review: 2026-10-20 / `review-4ad5ac744301bbda`

The selected generator remains version **3.3.0**. Final generator SHA-256 is
`99216a3011a7653571ee5539b6782bc5403d40f207bfab945fadeefdf02af6c6`;
the canonical rule hash remains `a84bb758c578`. This review changes no valid
nonnegative draw, canonical row, selected Racket authority, or keyed-randomness
version.

### Repair

The baseline accepted negative `sample_index` values because `_block_plan` fed
them directly into floor division and modulo. The schedule boundary now requires
an exact integer at least zero, so `generate`, `schedule_profile`, and
`schedule_spatial_witness` reject the same invalid provenance. A new portable
regression covers all three interfaces. The packet-owned historical fixture was
restored to its exact baseline hash and was not edited.

Final checks: 199 task tests passed; all 12 after-battery stages are green;
profile floor is 19/60 exact hits with all nine canonical inputs admitted; the
override gate has zero findings over 25,560 draws. Evidence is under
`checks/task-tests-final/` and `checks/after/` in this review return.

### Teaching contract and known limit

The normal public sampler remains intentionally ordered. In a 100-lessons-per-
band census, all 300 five-demo production lessons materialized successfully and
all ten declared rivals were refuted in every lesson. Arbitrary leave-one-pair-
out query rotation is **not** supported: 116/1800 rotations were ambiguous and
219 produced hook warnings. This does not invalidate the declared ordered
curriculum, but it forbids a claim that lessons may be freely reassembled.

The strongest canonical-fitting shortcut remains largest monochrome component
(or largest color bounding box): all canonical inputs have only one foreground
color. A current default witness at seed 17/index 3 has global mode color 3 split
into two five-cell components while color 1 has a six-cell component. The
canonical rule emits the color-3 L and the component rival emits the color-1
plus. Final-source Racket verification is retained under
`checks/current-counterexample/`.

### Proposed parametric extension

`workspace/parametric/` contains a separate proposed episode-level parameter,
`quarter_turns_clockwise` in `{0,1,2,3}`. The unchanged mode classifier first
selects plus/T/right-facing-L, then rotates the glyph. Setting zero is byte-
identical to the canonical program. Four complete Racket programs and retained
five-demo/two-query episodes pass Python/Racket parity and distinguish every
selected setting from all three rivals. This is a prototype only: it is not
catalog-approved or integrated into the production generator.

### Open findings and decisions

- Keep version 3.3.0 because valid generation is unchanged.
- Keep the negative-index guard at `_block_plan`, the shared schedule boundary.
- Preserve the ordered five-demo curriculum rather than redesign it incidentally
  for arbitrary rotations.
- Preserve the pre-existing archival Racket text divergence; selected authorities
  are synchronized and execution parity passes.
- Do not claim elimination of arbitrary finite-data shortcuts; evidence covers
  the ten declared rivals and the retained probes.

---

## Current revision: 3.3.0 — count versus spatial object size

This review starts from the already-integrated v3.2.0 baseline. Its control,
canonical-anchor, and endpoint repairs are retained, not claimed as new work.
The historical sections below describe that earlier repair, including its
Racket synchronization and its old retained evidence. **This v3.3.0 review
changes neither the canonical ledger nor the selected/archival authority file.**
Historical review ID: `review-5351bbba9e4bc5eb:v0001`; the supplied evidence index
and integration record are leads, not validation of these new generator bytes.

All nine canonical pairs have one foreground color, so largest 4-connected
component, largest 8-connected component, and largest color-bounding-box rules
all fit them. The baseline's existing seven-rival contract did not test these.
An independently retained Racket receipt confirms one baseline easy five-demo
lesson survives all three, with generated disagreeing examples elsewhere.
The exploratory 100-seed easy screen found 90, 93, and 70 surviving lessons,
respectively; this screen used input-count statistics, not public-sampler labels.
Its role was selecting a testable weakness, not establishing an authoritative
large-sample label result. The final public-Racket audit is separate.

### Constructive witness and lesson proof

Keep the three-index block and both original endpoint conditions. Choose which
mixed contrast is spatial with its own keyed random draw, independently of the
modal class, profile permutation, and which contrast has a modal endpoint.
For modal count M (8..32 within this subprofile), grow two connected modal pieces
in interior regions separated by a full row. When needed, add an isolated modal
corner. Each modal 8-connected component has size at most ceil(M/2).

Give a nonmodal color a connected boundary path of size ceil(M/2)+1 and enough
far corners to span the full canvas. Its total remains below M, even with
additional random cells. Its 4-connected maximum therefore beats every modal
8-connected component, and its bounding box beats the mode's strictly smaller
box. Both component-selection rivals and the bounding-box rival must disagree
with the unchanged modal rule. Secondary colors, counts, shapes, positions,
transpose, and orientation vary; at least five zeros are retained.

Every full block has one such witness and retains the old two-endpoint-condition
proof against seven rivals. Any five consecutive indices contain a full block.
Thus five unpinned, unrejected default demonstrations refute all ten declared
competitors and demonstrate each possible modal class. This is not a proof
against arbitrary rules fitted to finite examples.

### Restrictions and self-review

Only one of three draws uses the new structured spatial construction. Its
feasible canvases lie within 5..10 and its M range is 8..32; the other mixed draw
uses the previous free sampler, and every actual exact override uses the original
constructive override path. `None` values remain unpinned. Declared single-axis
support and explicit combination rejections remain covered by the override gate.
Versioned keyed randomness intentionally changes concrete seeded outputs.

Do not accidentally make spatial witnesses imply that the mode is absent from
scan endpoints: the separate choice permits both endpoint conditions. Independent
regressions cover all four spatial/nonspatial × endpoint-present/absent combinations
across all three modal classes and all difficulty bands. Small retained generated
examples in the current return use seed 17 / indices 3 and 1 (medium) for the two
spatial endpoint conditions. The boundary-heavy witness subprofile is deliberately
nonuniform; unrestricted random grid diversity is not claimed.

### Current evidence and tools

The current return retains 194 explicit task tests (168 original tests plus 26
new tests), a 240-test repository run, a fully green 12-stage battery, and a
source-bound Racket audit of 100 independent lessons plus 108 overlapping windows
per band. The ten current registry rivals fit all nine canonical pairs and are
refuted in every inspected final lesson. See the return's `checks/final-summary.json`
for exact hashes, unique-input denominators, seed ranges, and replay receipts.

`workspace/counterexamples.py` now emits four generated inputs: both original
controlled endpoint cases plus both default spatial endpoint conditions. It
refuses to overwrite retained evidence and checks generator replay, current
registry predictions, rule/source binding, input alignment, and successful
canonical outputs using a separately obtained supported Racket receipt. This
checks consistency of a receipt; it is not a cryptographic authenticity service.
The unchanged distribution tool automatically audits all current registry entries.

## Historical v3.0–v3.2 notes (retained)

## Authority and scope

The canonical program calls `(mode g 0)`: it ignores the literal color zero,
not an inferred background. All nine labeled canonical inputs are 5×5 with
one nonzero color. Consequently the demonstrations alone cannot distinguish
frequency from color presence or scanning order. Mixed-color generation is an
explicit extension supported by the existing Racket program. The canonical
program and its nine pairs remain unchanged.

The selected task-owned `racket_target.target_code` has been synchronized to
the exact canonical text. Its archival `raw_code` remains unchanged. The
before battery established execution parity despite the original text mismatch;
the synchronization is not a new rule or a new approval.

## Exact controls

`palette_size` now means all visible colors, including zero. The exact axes
are height/width 3..10, mode color 1..3, modal count 5..95, and palette size
2..6. All values are checked before any draw; booleans, floats and numeric
strings are rejected for these integer axes. `None` leaves an axis unpinned.

Unpinned geometry/counts adapt to valid pins. A combination must satisfy
`height * width >= mode_count + (palette_size - 2) + 5`. Failure identifies
the caller's incompatible axes. Placement preserves every drawn count;
there is no clamping, post-placement recoloring, or hidden fallback.
`observe_overrides` recovers the five axes from pixels.

Removed controls are rejected explicitly: `other_color` and `decoy_density`
were silently ignored; `texture` duplicated `cell_layout` and mixed invalid
examples into the valid domain. Layouts remain internal keyed randomness,
because a claimed construction label is not generally recoverable from pixels.
This is an intentional API revision: callers must migrate removed controls.

## Counting curriculum domain

At least five modal cells and five zero cells exclude trivial singleton,
four-cell, and nearly solid examples. The nine canonical pairs have modal
counts 8..14 and zero counts 11..17, so all remain admitted. This is a declared
teaching scope, not a claim that the unchanged Racket rule is undefined on
sparser inputs. In particular 3×3 canvases, ties, absent zero, modes 4..9 and
fallback all-zero outputs are outside this curriculum. Ties are excluded
because the rule does not supply a task-semantic tie policy.

`strict_canonical_like` means the declared task domain and checks the same
invariants as `self_check`. It does not mean exact 5×5/palette-two shape.
The independent canonical-profile gate and coverage probe measure that
separate distribution property.

## Teaching blocks and shortcut repair

Each block of three input indices gets independently keyed permutations of
classes 1/2/3 and profiles: canonical anchor, early decoy, late decoy. A full
block contains all three classes; its two mixed inputs contain 1,2,3 and have
different modal colors. Every contiguous five-input window contains a full
block, so five default demonstrations teach the three glyphs and refute the
declared first, last, smallest, largest, least-frequency, endpoint-complement,
and endpoint-limited-mode rules. This argument assumes no skipped/rejected draws and no overrides;
the public-sampler probe checks what is actually materialized.

An early-decoy example always starts with a distractor; a late-decoy example
always ends with a distractor. A separately keyed block coin chooses which
contrast has the true mode at its other endpoint. The second contrast has
both distractors at its endpoints, so its mode appears only in the interior.
Interior colors, counts, cells and layouts vary. The guarantees concern
unpinned default draws; an explicitly pinned three-color palette has only one
distractor and cannot realize this two-distractor contrast.

Version 3.0.0 put both distractors at both contrasts' endpoints, leaking the
mode as the missing core color. Version 3.1.0 repaired that mistake by putting
the mode at one endpoint of every contrast, but then a rival could count only
the endpoint colors. Each intermediate shortcut selected the observed mode
on 360/360 targeted draws. Version 3.2.0 mixes the two endpoint conditions
within every block and declares both rivals. The intermediate sources, probes,
failed regression checks, and first iteration's failed profile check are
retained. None is presented as final-source validation.

One binary anchor per block preserves canonical inputs without replaying
any fixed grid. Profile positions are randomized independently of classes,
so the anchor is not always the first example and class order is not periodic
across blocks. Difficulty changes geometry and distractor count weighting;
it does not invalidate an individually supported exact control.

## Evidence and limits

Correct generated labels are obtained only through canonical Racket execution.
Python glyph tables in named rivals and tests are predictions/expectations,
not generation authority. `lesson_identifiable` reads demonstration outputs
and query inputs; it does not use query labels. It checks the declared finite
rival set and demonstrated query class, not universal rule induction.

Run task-local tests explicitly; root pytest discovery does not include them.
The reusable distribution probe reads the current rival registries, verifies
each canonical-fit claim, distinguishes independently materialized lessons
from overlapping windows, records exact source hashes, and retains failures.
Use five demonstrations for training this curriculum. A shorter supplied solve
episode remains a useful visible-example attempt but has less teaching support.
## Current reviewer considerations

Source SHA-256: `99216a3011a7653571ee5539b6782bc5403d40f207bfab945fadeefdf02af6c6`.

# Decisions for review `review-4ad5ac744301bbda`

## D1 — Repair the schedule boundary, not each caller

**Prior behavior.** `_block_plan(seed, sample_index)` used `sample_index // 3` and `sample_index % 3` without checking the public index domain. Consequently `-1` was silently mapped into a valid negative block/residue schedule, and all three public schedule consumers accepted it.

**Decision.** Reject values for which `type(sample_index) is not int` or `sample_index < 0` at the top of `_block_plan`.

**Rationale.** `_block_plan` is the single source of schedule interpretation for `generate`, `schedule_profile`, and `schedule_spatial_witness`. One guard gives those interfaces the same contract and prevents future callers from bypassing a guard placed only in `generate`.

**Alternatives rejected.** Separate checks in each public function would duplicate policy and leave future call sites vulnerable. Normalizing with `abs`, clamping to zero, or permitting Python's negative indexing semantics would conceal caller errors and make seeded provenance ambiguous.

**Probe and failure mode.** The focused regression calls all three functions with `-1`. It failed against the baseline because no exception was raised, then passed after the one-location repair. Evidence: `checks/tdd-negative-index-red.log` and `checks/tdd-negative-index-green.log`.

**Limit.** This does not centralize validation across other generators; that is a shared-tool recommendation in `FEEDBACK_TO_CODEX.md`.

## D2 — Keep version 3.3.0 and preserve all valid draws

**Decision.** Do not bump `VERSION`, reseed keyed randomness, edit canonical rows, or alter the valid-output distribution.

**Rationale.** The patch rejects only values outside the declared nonnegative schedule domain. A version bump would unnecessarily change every seeded valid example and make the tiny contract repair look like a curriculum revision.

**Probe.** The complete after battery, 199 task tests, and current Racket counterexample verification bind the result to final generator SHA-256 `99216a3011a7653571ee5539b6782bc5403d40f207bfab945fadeefdf02af6c6`.

**Failure mode considered.** If an undocumented consumer intentionally used negative indices, it now receives a clear `ValueError` instead of a misleading valid lesson. That compatibility break is intentional because negative schedule provenance was undefined and strict defect lint already classified it as a defect.

## D3 — Put the regression in a new portable test file

**Decision.** Add `tests/test_negative_sample_index.py` using `reviewer_support.find_root`; do not edit the packet's immutable `test_generator_49754d8fa42e.py`.

**Rationale.** The assignment freezes baseline fixtures. A separate focused test keeps the patch reviewable and portable while preserving the fixture's exact uploaded SHA-256.

**Alternative rejected.** The first working draft added the assertion to the frozen fixture. That was reversed before task-test evidence was taken; the original file was restored byte-for-byte from the source archive.

**Limit.** The existing frozen fixture still triggers the linter's fixed-`parents[...]` portability warning. It is not repaired because doing so would violate the immutable-fixture clause; this is reported as feedback F3.

## D4 — Use episode-level glyph rotation as the parametric prototype

**Decision.** Propose `quarter_turns_clockwise ∈ {0,1,2,3}`, fixed across an episode and applied after the unchanged mode-color classifier selects its plus/T/L glyph.

**Rationale.** The parameter is discrete, bounded, easy to express as complete Racket programs, preserves the core task mechanism, and leaves setting `0` byte-identical to the canonical rule. Five demos can cover all three classifier classes, and T/L queries distinguish all four settings.

**Alternatives considered.** Changing output color would be too superficial and could be inferred independently of the classifier. Permuting the color-to-glyph mapping would entangle the original semantics and make the default harder to audit. Variable output size or per-example rotation would change more than one concept and weaken episode-level learnability.

**Probe.** `workspace/parametric/verify.py` executes all four complete Racket rules on retained demonstrations and queries and records exact source/program hashes in `checks/parametric/verification.json`.

**Limit.** The prototype is proposed, not integrated, approved, or evidence that arbitrary programs are excluded. Public challenge files intentionally omit hidden settings and query outputs.

## D5 — Preserve the ordered teaching contract; do not claim rotation robustness

**Decision.** Accept the normal ordered sampler after 300/300 lessons refuted all ten rivals, but report leave-one-pair-out query rotation as unsupported.

**Rationale.** The generator's existing teaching proof is explicitly block/order based: every five consecutive default demonstrations contain a complete three-index block. Reassembling one of those pairs as the query removes evidence the hook assumed would stay in the demonstrations. Redesigning that curriculum was unrelated to the negative-index defect and would be a much larger semantic change.

**Alternatives rejected.** Calling the required-rotation census a pass would be false. Redesigning every five-demo set to remain identifiable after removal of any pair might be valuable, but it would require a new schedule proof, new distribution study, and likely a version bump; it is not a safe incidental repair.

**Evidence.** Ordered production: 0/300 ambiguous. Rotations: 116/1800 ambiguous and 219 hook warnings. The required-policy report is retained at `checks/lesson-census.json`; the diagnostic interpretation is retained at `checks/lesson-census-ordered.summary.json`.

**Limit.** The random census is finite and does not exhaust all cyclic lesson starts. The generator declares no schedule-period census contract.

## D6 — Answer the shortcut question with a current generated Racket witness

**Decision.** Use the strongest simple canonical-fitting rival, “choose the color with the largest 8-connected monochrome component,” and a final-source default example at seed 17/index 3.

**Rationale.** Every canonical input has only one foreground color, so the rival fits all nine canonical demonstrations. The generated witness makes color 3 the global mode while splitting it into two five-cell components; color 1 has a six-cell component. The intended rule returns the color-3 L, while the rival returns the color-1 plus.

**Probe.** `workspace/counterexamples.py` regenerated the input from final source, the packet's Racket bridge produced the canonical output, and the verifier checked generator/source/rule hashes plus all declared rival disagreements. Evidence: `checks/current-counterexample/generated.json`, `checks/current-counterexample/racket.json`, and `checks/current-counterexample/verified.json`.

**Limit.** This refutes the named rival; it does not prove uniqueness against all possible finite-data rules.

## D7 — Treat prior v3.3.0 return material as context, not proof

**Decision.** Retain the historical notes and tools, but rerun source-bound tests, the battery, the census, Racket counterexamples, and the reviewer solve against the bytes in this packet.

**Rationale.** Earlier evidence was tied to earlier review identities and could not establish the final hash after this repair.

**Limit.** Historical archival authority text remains divergent from the selected canonical text, although execution parity passes. No historical file is rewritten in this review.
