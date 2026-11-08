# Working notes: 56f043832ecb

## Current native candidate — enclosed-area selection, 2026-10-25

Assignment `review-33e7910032bf51b6` adds a separate native family under
`workspace/parametric/`. Production version **4.0.0**, its source
`45c8d0040b5a201132ac5bf3b5157e3a10053dbb7cce1ef67d803945affbbc5c`, the selected
canonical program and existing approval/audit records are unchanged. The default
program is preserved byte for byte: SHA-256
`29fbeb2dce8331b5f74431c79d5a108a3e6172021c019bb0775f2c0c701d4083`.

### Native rule and domain

The episode-fixed parameter is `selection=all|largest|smallest`, default `all`.
Discover four-connected monochrome components and compute each component's
enclosed-cell mask with the canonical component-local bbox flood fill. `all`
uses the exact canonical program. The other settings rank **total enclosed cell
area**, exclude zero-hole components, retain every tied extremum, and fill each
selected object's holes with its own color. Disconnected objects sharing a
color remain separate candidates.

A produces the input-dependent hole masks and their areas; B needs those areas
to select which components to paint. This is a derived-measurement selection
dependency, not an iterative simulation. Substituting wall-cell counts while
retaining actual hole masks and paint logic changes a qualified largest output
in **13 cells**, and a qualified smallest output in **one cell**; both programs
and both labels were independently replayed through protected Racket.

The API supports **3–6 demos and 1–4 queries independently**, exact integer seeds
`0..2**63-1`, and strict literal 1–30 by 1–30 integer grids. Omitted settings use
`seed % 3`, not necessarily the canonical default. Each call constructs the same
six-demo/four-query input bank before slicing, with an independent query-order
stream and inputs matched across settings. Returns are fresh and global RNG
state is unchanged. Generation uses explicit rectangle, thick-wall, spur,
concave L-shell, multi-cavity, leaking and solid shapes in separated bbox slots.
It does not claim arbitrary topology coverage. Nested foreign-color objects
remain outside the generated grammar: the canonical component-only algorithm
can paint over such cells, and the mirror deliberately preserves that behavior.

### Teaching decisions and repairs

The mandatory demonstrations have positive cavity totals **[2,6]**,
**[1,1,4,6,6]**, and **[3,4,9,12,12]**. They distinguish area from wall/bbox size,
cavity count and largest individual cavity; teach both extrema ties; and cross
repeated colors with different component areas.

Two concrete authoring gaps were found and repaired within the original
**three-demo budget**, without removing query branches:

* Early irregular components were never selected by the largest setting. A rule
  requiring a complete rectangular bbox perimeter fit all three demos and
  changed **3 cells** on seed 0's query and **6 cells** on seed 17's query. Spurs
  now win both extrema, and concave L shapes supply a minimum and a tied maximum.
* The first placement policy put every compulsory-demo object on a canvas edge.
  A border-only rule fit the lesson and missed **12 cells** for seed 0 / all and
  **one cell** for seed 17 / smallest. Original source and executed alternatives
  are retained. Role-aware placement now puts both a minimum and maximum target
  strictly inside the canvas, with their tied counterparts on its border. D1
  alone contains one interior and one boundary winner for each extremum.

The final audit tests both `border_only` and `skip_border`, with a protected
two-frame regression that verifies their opposite predictions. Two authored
two-demo prefixes for `smallest` also retain a largest-single-cavity alternative
that changes **7 cells** on the third input. They explain the three-demo minimum;
they are private alternative-answer research examples, not admitted ambiguous
single-answer exports. These are not claims about old production lesson assembly.

Queries include small and medium scenes, a side exceeding 20, and substantive
**30×30** content: nine components, **259 nonzero input cells**, objects on all
four boundaries, and total hole areas `[0,1,1,8,12,12,20,20,42]`. Query roles are
shuffled once per seed while preserving one-query/four-query first-turn equality.

### Current verification and owner handoff

Final sampler SHA-256:
`df32bebe02c3790d1879f4a820b18c5af8f872cc54a9fa8ade236b1866f98197`.
**87 adapter tests and 23 audit/export tests pass**; the latter include six
protected evaluations of the two boundary rivals. `checks/56f043832ecb/audit-r2/`
records six episodes at seeds 0/17, 42 intended generated labels, all four
canonical labels plus explicit-all cross-checks, and **110 rival comparisons**:
**106 demo-refuted**, four agreeing on all checked queries, zero errors or
query-disagreeing survivors. It used **288 unique protected executions**, with
108 cache hits, and validated all **24 one-query public files**. The four benign
survivors remove the positive-area filter under all/largest; no universal
identifiability or training-gain claim is made.

The native inventory is `workspace/parametric/evidence/manifest.json`.
`checks/56f043832ecb/qualification-r2/{qualification,execution}.json` records
**6/6 qualified jobs** across all settings and two seeds, with 78 protected
evaluations. `checks/56f043832ecb/causal-r2/{witness,replay}.json` records the
wrong-intermediate replay. Earlier `audit-r1`, `qualification`, `causal` and
development receipts are retained as superseded evidence, not current-source
qualification. Original gaps are in `rectangle-gap-r1.json` and
`border-gap-r1.json`; compact source-bound sampler facts are in
`sampler-facts-r2.json`. No unaffected production battery was rerun.

Reviewer status is **ready; owner acceptance pending; training not admitted**.
After integration, the owner must qualify and accept the exact live native
source. Public filenames hash only visible demos and the current query input;
settings, reference programs, answers, seeds, ordinals and future queries remain
private. The existing consumer reveals the four queries one at a time.

## 2026-10-02 review `review-1d0864e5c9b2c933`

### Authority and scope

The selected Racket rule was not changed. The canonical title (“Fill each enclosed hole with its frame color”), written solution (“For every hollow same-color object…”), `topology`/`holes` skill tags, and bbox-local flood-fill program jointly support a topological rule broader than the rectangular appearance of the four official inputs.

The generator now admits exactly one additional positive family: remove one outward spur and the component must be an exact closed rectangular perimeter. This conservative family creates a source-grounded rectangle-only counterexample while preserving an auditable grammar. Arbitrary closed curves, multiple protrusions, interior contamination, mixed-color walls, and disconnected walls remain outside this generator’s teaching contract even where the selected Racket program may define an output.

### Distribution decisions

Every three consecutive ordinary sample indices contain:

1. `canonical_pair`: two canonical-palette rectangular targets at the official 7–8 by 8–11 scale; at least one target touches the canvas border.
2. `open_decoy`: a positive target plus a one-gap leaking rectangle.
3. `irregular_broad`: a broad-palette spurred target.

This fixes the prior hard-band zero strict-profile support while ensuring every lesson window contains concrete counterexamples to largest-only, bbox-fill, rectangle-only, canonical-color-only, identity, and border-skip rules. Explicit overrides still win over schedule defaults.

### Executable review contract

`rule_mirror` implements the selected Racket program’s bbox-local border flood-fill criterion. `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS` convert shortcut claims into executable checks. Unknown override keys now raise `ValueError` instead of being silently ignored.

The task-local pytest suite pins the exact spurred family, rejects two-cell protrusions and interior contamination, checks schedule coverage and hard strict support, verifies every named witness/rival disagreement, verifies every declared canonical shortcut against all official pairs, and proves every cyclic three-demo window eliminates all lesson competitors.

### Remaining limitation

The generated irregular evidence is intentionally one-step beyond rectangles, not a comprehensive sample of all topologically valid hollow objects. It proves that “rectangle” is not the rule, but it does not exhaustively teach multiple holes, deeply concave walls, or arbitrary closed curves. Expanding farther should add one exact family at a time with a corresponding canonical-shortcut probe and Racket parity evidence.

Imported associated notes remain in `evidence/associated_notes.jsonl`; this review supersedes the rectangle-only teaching limitation while retaining its caution against unbounded shape expansion.
## Current reviewer considerations

Source SHA-256: `45c8d0040b5a201132ac5bf3b5157e3a10053dbb7cce1ef67d803945affbbc5c`.

# Design decisions for `56f043832ecb`

This document records each material input-distribution choice, the inherited rationale where available, alternatives considered, the probe used, and the remaining failure modes. “Inferred” means the old code made the choice but did not preserve an explicit rationale.

## D1. Keep the selected Racket rule unchanged

**Choice.** Preserve rule hash `29fbeb2dce83`; change only the Python generator and its tests/docs.

**Original rationale.** The retained associated note says the canonical `program_solution` and selected target are exact-synchronized, while a divergent archival text is execution-equivalent and should not be promoted implicitly.

**Alternatives considered.** Rewrite the Racket rule for rectangles; rewrite it for a new irregular grammar; or synchronize to the archival text.

**Probe.** Authority sync passes, all four canonical pairs pass, and after rule smoke applies the selected rule to 120/120 draws with no crash, mutation, or out-of-range output. Python mirror parity is 120/120.

**Failure modes / limitation.** If the selected Racket program itself has an unseen semantic defect, generator-only work cannot correct it. The canonical evidence and parity checks currently give no reason to change it.

## D2. Interpret the rule as topology, not rectangularity

**Choice.** Treat “fill holes of hollow same-color objects” as the semantic authority. Rectangles are an input family, not the rule definition.

**Original rationale.** The title, written solution, `topology`/`holes` tags, and Racket flood-fill implementation all say or implement enclosure. The prior generator intentionally added an open-frame negative witness for the same reason.

**Alternatives considered.** Stay rectangle-only because all official grids are rectangular; or admit arbitrary closed shapes immediately.

**Probe.** The rectangle-only rival fits all four canonical pairs but disagrees with every scheduled one-spur witness; the semantic gate verifies 60/60 such disagreements.

**Failure modes / limitation.** The source examples alone do not visually demonstrate arbitrary topology. I therefore admitted only one exact, auditable irregular family rather than all Racket-valid shapes.

## D3. Positive shape grammar: rectangles plus one outward spur

**Choice.** A positive component is either an exact closed rectangular perimeter or an exact rectangle plus one outward 4-connected cell. Removing that cell must recover the rectangle exactly.

**Original rationale.** Rectangle-only scope was an explicit prior limitation. The one-spur family is new and chosen as the smallest counterexample to rectangularity.

**Alternatives considered.** Concave polygons, arbitrary random walks, multiple spurs, multiple holes, or no irregular positives.

**Probe.** Regression tests accept and fill a one-spur frame, verify exterior cells in the expanded bbox remain zero, reject a two-cell protrusion, and reject interior contamination. Rule mirror/Racket parity is 120/120.

**Failure modes / limitation.** This family may still encourage a “rectangle plus optional spur” recognizer. It is intentionally a first controlled extension, not a complete topology curriculum.

## D4. Negative shape grammar: exactly one non-corner wall gap

**Choice.** Retain at most one open rectangular decoy, made by deleting exactly one non-corner perimeter cell.

**Original rationale.** Retained note `open_frame_negative_witness` states that canonical pairs do not falsify bounding-box fill; a visually close leaking perimeter does.

**Alternatives considered.** Larger gaps, missing corners, broken irregular walls, or no negative example.

**Probe.** `rule_mirror` leaves the decoy unchanged; the bbox-fill rival differs on every checked open-gap witness (60/60). The test suite also checks an open-only frame has no local fill target.

**Failure modes / limitation.** One-gap rectangles do not cover every way an apparent enclosure can leak. They are preferred because the visual contrast is controlled and the intended answer is unambiguous.

## D5. Three deterministic curriculum profiles

**Choice.** `sample_index % 3` selects `canonical_pair`, `open_decoy`, or `irregular_broad`. Every three consecutive ordinary indices contain all three.

**Original rationale.** The baseline already used a three-slot schedule to guarantee some two-frame and open-decoy coverage. The new schedule makes the full teaching contract explicit.

**Alternatives considered.** Pure random sampling; seed-dependent profile selection; longer cycles; or enforcing contrast only statistically.

**Probe.** Unit tests check every sliding three-index window. The semantic census observes 196 / 199 / 205 pooled samples for the three profiles, with all profiles represented in every band. All 12 sampled lessons eliminate all six competitors.

**Failure modes / limitation.** The guarantee assumes lesson builders use consecutive sample indices. Exporters that subsample arbitrary indices can break the local window guarantee; the pooled distribution still remains balanced.

## D6. Canonical-pair profile uses two positives

**Choice.** The canonical anchor has two closed rectangular targets, no decoy, and canonical colors.

**Original rationale.** Official examples include both one- and two-object scenes. The previous schedule deliberately used a two-frame slot to refute “fill only the largest object.”

**Alternatives considered.** One target only, three targets, or random count in the anchor.

**Probe.** The largest-only rival disagrees on 60/60 `two_closed_objects_fill` witnesses. The profile-floor exact rate rises from 4/60 to 15/60.

**Failure modes / limitation.** Two objects do not test nesting or same-color disconnected objects; distinct colors and moats keep component ownership clear.

## D7. One strict canonical anchor in every difficulty cycle

**Choice.** `canonical_pair` draws height 7–8 and width 8–11 in easy, medium, and hard. Other profiles retain wider difficulty-specific ranges.

**Original rationale.** Axis bounds were inherited from the canonical neighborhood: official shapes are 7×9, 7×10, 8×8, and 8×11. The exact reason for the prior hard-only enlargement was not recorded.

**Alternatives considered.** Preserve hard at 9–10 by 10–12; make every sample canonical scale; or eliminate difficulty-dependent size.

**Probe.** Before hard support was 0/20 exact and 0/20 envelope. After it is 5/20 exact and 8/20 envelope; all bands pass.

**Failure modes / limitation.** One-third canonical anchors reduce the size distinction between bands. The other two profiles still carry the larger hard geometry.

## D8. Force a border-touching positive in the canonical anchor

**Choice.** At least one closed rectangle in `canonical_pair` touches a canvas border.

**Original rationale.** Inferred from the need to disprove implementations that confuse canvas reachability with component-local bbox reachability; the old code had a border-touch witness but no executable claim.

**Alternatives considered.** Leave border contact random; force it only in a special fourth profile; or remove the witness.

**Probe.** The `skip_border_touching_closed_frames` rival differs on 60/60 checked witnesses and is eliminated in every sampled lesson.

**Failure modes / limitation.** Border contact is strongly coupled to the canonical profile. A learner could partly associate “border” with the two-frame slot, though the true rule is still directly demonstrated.

## D9. Palette split: canonical and broad

**Choice.** Canonical profiles use colors `(2,3,4,6,7)`; the irregular profile uses `(1,5,8,9)`. Components in a scene have distinct colors.

**Original rationale.** The five-axis contract and palette observability were retained intentionally. The exact old color partition rationale was not documented; it appears intended to separate source-like colors from broader ARC colors.

**Alternatives considered.** One unrestricted palette; random mixed canonical/broad colors; or canonical colors only.

**Probe.** `observe_overrides` recovers palette kind exactly. The canonical-colors-only rival fits all official pairs but disagrees on 60/60 broad-palette witnesses. The override matrix accepts all 9,360 expected draws.

**Failure modes / limitation.** Because irregularity and broad palette co-occur in ordinary scheduled draws, those two cues are correlated. The declared rival checks each semantic behavior, but a larger future curriculum should sometimes cross irregular shapes with canonical colors and rectangles with broad colors.

## D10. Separate components by a one-cell moat

**Choice.** Keep components Chebyshev-separated by at least one zero cell and use a distinct color per component.

**Original rationale.** Inferred from the old layout and self-check: it makes same-color component extraction and visual ownership unambiguous.

**Alternatives considered.** Diagonal contact, adjacent different colors, nested objects, or repeated colors.

**Probe.** Mutation-sensitive self-check and targeted tests reject touching components. Rule smoke has no crashes or input mutation.

**Failure modes / limitation.** The distribution does not teach how the rule behaves with nested, touching, or repeated-color objects, even though some such cases may be defined by the Racket object extractor.

## D11. Explicit overrides win; unknown overrides fail

**Choice.** Scheduled defaults are inserted only with `setdefault`; any declared explicit override takes precedence. Any undeclared key raises `ValueError` before `gen_ctx` is called.

**Original rationale.** Retained note `minimal_observable_axes` says only literal, independently recoverable axes should remain and exact override agreement should be required. Unknown-key behavior was previously unspecified and proved unsafe.

**Alternatives considered.** Silently ignore unknown keys; warn only; or prevent overrides that conflict with a schedule profile.

**Probe.** The after override checker executes 104 cases and 9,360 accepted draws with zero warning/finding. The typo probe is rejected. Unit tests pin both unknown-key failure and schedule behavior.

**Failure modes / limitation.** An explicit override can intentionally collapse a profile’s contrast—for example, request no decoy in the open slot. The three-profile guarantee therefore applies to ordinary draws, not arbitrary diagnostic override combinations.

## D12. Make semantic claims executable

**Choice.** Add a Python `rule_mirror`, six rival implementations, witness-to-rival mappings, lesson competitors, and three canonical shortcuts.

**Original rationale.** The baseline had named witnesses and a lesson hook, but no rival functions; the before gate showed that this made success vacuous.

**Alternatives considered.** Keep prose-only witness names; rely only on human montage review; or run a model-based solver as the gate.

**Probe.** The after gate finds no weak witnesses, checks each of six rival claims 60 times with zero violations, verifies 12/12 lessons, and finds generated counterexamples for every declared canonical-fitting shortcut.

**Failure modes / limitation.** The rival set is finite. An unanticipated shortcut can still survive. Future audits should add a rival whenever a new shortcut is found rather than only adding prose.
