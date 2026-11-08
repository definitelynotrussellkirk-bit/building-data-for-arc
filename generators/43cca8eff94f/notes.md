# Current decisions: 43cca8eff94f

## Intended rule and authority

Keep the selected Racket rule unchanged and pin `RULE_HASH = "ced1f6ce57f8"`.
The cyan (8) component is fixed. The connected red (2) object translates
rigidly in the unique cardinal direction toward it until the next step would
intersect the cyan component or leave the grid.

## 2026-10-12 repair

The selected v2.0.1 source used solid cyan blocks, advertised eight axes while
honoring only part of them, accepted unknown controls, and had a two-condition
`self_check`. Prior audit `review-19294e16c5494e4c:v0001` was used as the lead
for the dead exact-control defect; its bound source hash was
`4167909a3241db96f1f30e3ecaca9f6cea32be088d45c855872dfcfdc1fe3034`.

Version 3.0.0 reverses those choices:

- Generate one canonical hollow rectangular cyan frame, not a solid block.
- Expose only five exact, pixel-observable axes: `grid_h`, `grid_w`,
  `direction`, `obj_size`, and `gap`; all legal extrema are constructive.
- Reject unknown controls, coercible scalar overrides, invalid sample indices,
  and difficulty values outside `None|easy|medium|hard`.
- Generate a connected 3..7-cell red polyomino inside a 3x3 box and align a
  leading-edge cell with the frame lane, so the observed gap equals the actual
  number of legal slide steps.
- Validate rectangularity, integer colors, exact palette, component counts,
  hollow-frame topology, object connectivity/size, clean direction, gap, and
  docking target. Canonical pairs are accepted by the same validator.
- Use the five-index schedule `right,left,down,up,up`. With four demos and one
  query, every cyclic five-example lesson retains an `up` demonstration even
  when an `up` example is held out.
- Declare the canonical-fitting `no_up` rival plus an executable `up_direction`
  witness. This is a finite-rival teaching contract, not proof of unique human
  induction.

The portable independent geometry/oracle helper is
`workspace/reference_probe.py`; focused regressions are in
`tests/test_generator.py`.

## Deliberate limits

The sampler is narrower than the raw Racket program: colors remain 0/2/8,
frames are hollow rectangles with side lengths 3..6, objects fit a 3x3 box, and
gaps are 1..3. These limits preserve the canonical concept and make every
public control jointly constructive. The reference rule itself can process
broader blockers and shapes, but those are not claimed as this generator's
training domain.

Only the `no_up` shortcut is declared. Passing it, the fixed-seed schedule
census, and generic checker rivals does not rule out every plausible alternate
rule. Any future expansion should add an independently executable rival and a
scheduled witness before widening the domain.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-19294e16c5494e4c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `4167909a3241db96f1f30e3ecaca9f6cea32be088d45c855872dfcfdc1fe3034`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Ignored dimension/object/gap controls on baseline4167909a3241 addressed by acceptedd2616 returnfc7217aa7f21: exact5observable axes and strict supported domains,65 reported portable tests plus12/12 battery. This closes exact-control finding; new undeclared morphology questions remain separately reviewable.

### Assessment or prior finding

## 43cca8eff94f

**Reproduced contract defect: advertised exact overrides are ignored.** With generator SHA-256 `4167909a3241db96f1f30e3ecaca9f6cea32be088d45c855872dfcfdc1fe3034`, I called seed 7, sample index 0, difficulty `easy`, requesting `grid_h=20`, `grid_w=24`, `direction=right`, `obj_size=7`, and `gap=5`. The returned grid was 12×14 with only three color-2 cells; `self_check` nevertheless returned no errors. The input is lawful for the Racket rule, and `arcpuzzles apply` executed rule hash `ced1f6ce57f8` successfully.

The generator reads only `direction` and degenerate `texture` from overrides; the other advertised controls are randomized. This is a concrete override-contract failure, not merely a suspected shortcut. Evidence: `checks/audit/43cca8eff94f/probe.json`, `input.json`, and `racket.json`. I left the audit target unchanged as required.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-19294e16c5494e4c-v0001/audit_assets.json), manifest SHA-256 `68a7fc8b92360b7b7506a55b59be8486745d4fddf7dd95c67fa8968e036d82b2`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `fc7217aa7f21bf87864b23620caa1c5ca58a3fc1ca2f6b84c66852ee0f37cb43`.

# Decisions for 43cca8eff94f

Final generator SHA-256:
`fc7217aa7f21bf87864b23620caa1c5ca58a3fc1ca2f6b84c66852ee0f37cb43`.
The selected Racket authority was not edited; its catalog rule hash remains
`ced1f6ce57f8`.

## D1 — Keep the authority; pin it in Python

**Prior choice.** Version 2.0.1 omitted `RULE_HASH`, so source/rule drift could
escape a task-local assertion.

**Decision.** Keep the existing Racket rule unchanged and add
`RULE_HASH = "ced1f6ce57f8"`. Authority synchronization and Racket lint both pass
in `checks/after-final/`.

**Rejected alternative.** Editing the rule to match the old solid-block sampler
would have changed the authoritative task merely to preserve a defective
sampler. The canonical examples and existing rule already express the intended
slide-to-contact transformation.

## D2 — Restore canonical hollow-frame morphology

**Prior choice.** The baseline generated solid cyan rectangles despite canonical
inputs using hollow cyan frames. Its weak self-check did not distinguish them.

**Decision.** Construct exactly one hollow rectangular color-8 frame, side lengths
3–6, and validate border completeness, empty interior, connectivity, palette,
and component count. This preserves the canonical visual concept while remaining
constructive at every supported size.

**Rejected alternative.** Treating arbitrary cyan blockers as equivalent would
broaden the rule domain but would not guarantee that training data teaches the
canonical “frame” concept. Such an expansion needs explicit topology profiles and
rivals first.

**Evidence.** Focused morphology regressions are in
`repo/generators/43cca8eff94f/tests/test_generator.py`; final profile and grammar
receipts are under `checks/after-final/`.

## D3 — Replace aspirational axes with five exact observable controls

**Prior choice.** Version 2.0.1 advertised controls that were ignored,
unobservable, singleton, or only partially honored. Unknown keys were silently
accepted.

**Decision.** Expose only `grid_h`, `grid_w`, `direction`, `obj_size`, and `gap`.
Each legal value is recoverable from pixels and jointly constructive. Reject
unknown keys, booleans/coercible scalar impostors, invalid sample indices, and
difficulty values outside `None|easy|medium|hard`.

**Rejected alternative.** Keeping decorative axes for metadata compatibility
would continue to claim distinctions not present in the generated input. Alias
controls were also rejected because two names for one latent variable weaken
exact-override auditing.

**Evidence.** `workspace/reference_probe.py` independently recovers all five
axes. The strict override and defect-lint stages pass in `checks/after-final/`;
the intermediate numeric-difficulty failure remains in `checks/after/`.

## D4 — Use constructive geometry with a measurable gap

**Decision.** Draw a connected 3–7-cell red polyomino inside a 3×3 box. Place a
leading-edge object cell in the frame's approach lane, and choose the source
position so `gap` equals the exact number of legal one-cell translations before
the next step would overlap cyan. The validator independently checks object
connectivity, clean cardinal direction, measured gap, and final docking target.

**Rejected alternative.** Rejection sampling arbitrary placements was simpler but
could make legal override combinations rare or impossible and could silently
bias directions near small grids. Constructive placement makes extrema and joint
controls testable.

**Probe.** `repo/generators/43cca8eff94f/workspace/reference_probe.py` contains an
independent Python slide oracle rather than calling the Racket implementation.

## D5 — Schedule all four directions and retain an upward witness

**Prior choice.** Canonical examples did not force upward movement, so the
canonical-fitting rival “perform the move except when the object is below the
frame” remained viable.

**Decision.** Use the five-slot direction schedule
`right,left,down,up,up`, with four demonstrations and one query. Two upward slots
ensure that every cyclic holdout of one labelled pair leaves at least one upward
demonstration.

**Rejected alternative.** A four-slot one-of-each schedule fails when the sole
upward example is the held-out query. Pure random directions offer no finite
lesson-level guarantee.

**Evidence.** The strict semantic stage executed all five starts and every query
rotation at fixed seed 0: 15 lessons and 75 rotations, all green. See
`checks/after-final/checks/43cca8eff94f_after_semantic_gate.json` and its schedule
census receipt.

## D6 — Declare a finite executable rival contract

**Decision.** Add the `no_up` rival, an `up_direction` witness, and
`lesson_identifiable`. Keep the same callable bound through
`SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS` so tools can
inspect one actual hypothesis rather than a prose-only warning.

**Limitation.** Refuting this finite rival is not proof of unique human induction.
The final 300-lesson census found no ambiguity under declared and generic checked
rivals, but unmodeled shortcuts can still exist.

## D7 — Make self-check a task-domain validator, not a smoke assertion

**Decision.** Validate rectangular integer grids, exact palette, one connected red
object of legal size, one hollow cyan frame, no accidental contact, one clean
cardinal approach, exact measured gap, and a legal authoritative docking result.
Accept the canonical pairs under the same domain logic.

**Rejected alternative.** Merely checking that colors 2 and 8 occur would let
solid blocks, disconnected objects, ambiguous direction, or impossible docking
enter the dataset while still producing some Racket output.

## D8 — Preserve canonical-size support without collapsing diversity

**Decision.** Schedule canonical dimension/frame profiles into the finite lesson
cycle, while allowing broader legal grids and shapes elsewhere. This gives every
band measured canonical-envelope support without making all examples copies of
the canonical boards.

**Evidence.** The final profile floor sampled 60 draws with zero crashes and 45
exact canonical-profile hits; all bands had support. Diversity and distribution
stages are green in `checks/after-final/`.

## Deliberate limits and future expansion

The final sampler fixes colors to 0/2/8, frame side lengths to 3–6, object size to
3–7 within a 3×3 bounding box, and gap to 1–3. The Racket rule can process a
broader domain, but this generator does not claim that broader coverage. Before
adding colors, irregular blockers, larger shapes, diagonal arrangements, or
longer gaps, add pixel-observable exact controls, canonical morphology coverage,
and at least one executable rival whose witness is guaranteed by lesson assembly.

## 2026-10-24 native parametric return

Status: **ready for owner native intake; not accepted and not training-admitted**.
The task-local adapter adds one episode-fixed parameter, `finish`, with settings
`dock_only` and `contact_projection`. `dock_only` returns the exact canonical
program bytes (`ced1f6ce57f8faebda0646ea835fbcd7a1a2b84f5ad604224d8980565772c31c`).
The alternative first docks the red polyomino, derives the exact post-dock
red/cyan contact set, then projects yellow rays from those touched frame cells
through the hollow interior.

The dependency is non-cosmetic: B's ray seeds do not exist before A computes the
input-dependent docking result. The protected-Racket wrong-order witness at
`checks/43cca8eff94f/sequential-witness/witness.json` changes the final grid when
projection is attempted before docking; its replay is `reviewer_replayed`.

Qualification at `checks/43cca8eff94f/qualification/qualification.json` passed
both settings on seeds 0 and 17 with three demonstrations and four novel queries
per episode (28 protected-Racket labels total). The adapter supports 2..6 demos,
1..4 queries, deterministic count prefixes, all four directions, and a substantive
30x30 query. The bounded authoring probe tested 30 generated cases and refuted
both the bounding-box-span and project-before-dock rivals on all 30. This is only
a finite rival result, not universal identifiability. Owner integration must
re-run native qualification and acceptance on exact live bytes.

