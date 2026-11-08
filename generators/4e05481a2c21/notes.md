# Working notes: 4e05481a2c21

## Review finding

The imported version 2.1.0 produced only rectangular holes.  Consequently the
simple rival “fill each hole union's bounding box” matched every generated
example as well as all three labeled canonical pairs.  Two additional rivals
also fit the canonical pairs: “keep only the largest enclosed region” and
“treat every zero in an object's bounding box as a hole.”  The baseline also
lacked `RULE_HASH`, accepted unknown override keys, advertised dead or
non-independent controls, and had no executable semantic lesson contract.

## Repair

Version 3.0.0 keeps the canonical two-object grammar and introduces
`rectangle`, `notched`, and `split` hole profiles.  Complex profiles use a 5x5
ring, modify the enclosed topology without opening it, and omit one outer
corner.  The omitted corner is an exterior bounding-box zero, so it refutes the
“all bbox zeros” rival while preserving a valid enclosed region.

The five-pair schedule is:

```
notched, split, notched, split, rectangle
```

A lesson uses four demonstrations plus one query.  Holding out any one pair
therefore leaves both a notched witness and a split witness visible.  The
module now pins `RULE_HASH = "e13b35a51ff4"`, rejects unknown or ill-typed
overrides, reports exact realized axes with `observe_overrides`, implements a
robust validator, and declares executable rivals, witnesses, and lesson
identifiability checks.

## Independent reviewer tooling

`workspace/reference_probe.py` independently derives components, bounding
boxes, enclosed regions, the reference transformation, all three rivals, and
visible override observations.  It does not import transformation helpers from
the generator under review.  The task-local tests use the portable
`reviewer_support` canonical-data API.

## Verification snapshot

Final generator SHA-256:
`5c48db7df2d19349f48317ba6ccc18aaa4234323eb24ffd198945fc8fdb89547`.

- Task-local tests: 79 passed, 0 failed.
- Final battery: 12/12 stages green.
- Required-rotation semantic gate: passed.
- Lesson census: 300/300 lessons materialized, 1,500 pairs and 1,500 query
  rotations checked, 0 ambiguities, 0 scoring/materialization errors.
- Exhaustive task-local schedule test: all five cyclic starts and every query
  position distinguish all three declared rivals.
- Racket authority was not changed; selected rule hash remains
  `e13b35a51ff4`.

These finite checks establish the declared teaching contract, not uniqueness
against every conceivable hypothesis.
## Current reviewer considerations

Source SHA-256: `5c48db7df2d19349f48317ba6ccc18aaa4234323eb24ffd198945fc8fdb89547`.

# Decisions: 4e05481a2c21

## D1 — Preserve the canonical two-object grammar

**Original rationale:** The imported summary described exactly two separated
hollow objects at canonical scale.  No retained note justified changing object
count, output order, or palette semantics; the original rationale is otherwise
unknown.

**Decision:** Keep a zero background, exactly two separated four-connected
objects in distinct colors, 3..5-cell object bboxes, and left-to-right output
ordering on 5..8 by 10..16 canvases.

**Alternatives considered:** Add three or more objects, allow touching objects,
or vary the packing order.  Those increase surface diversity but do not address
the observed shortcut and risk drifting from the canonical task.

**Probe/failure mode:** Canonical profile and authority stages verify scale and
rule support.  The limitation is intentional: this generator does not claim to
teach object segmentation when same-color objects touch.

## D2 — Vary enclosed topology, not cosmetic texture

**Original rationale:** Version 2.1.0 exposed a `texture` control, but all lawful
outputs still had rectangular holes.  Its values were overlapping or partly
dead, so the control did not change the semantic evidence.

**Decision:** Replace texture with one exact `pattern_kind` axis:
`rectangle`, `notched`, or `split`.  `notched` makes a connected
nonrectangular hole; `split` makes multiple enclosed regions.

**Alternatives considered:** Randomly punch interior cells, use arbitrary
polyomino frames, or retain decorative texture.  Arbitrary punching can open a
hole to the exterior or split the colored object; decorative texture leaves the
shortcut intact.  Fixed topology constructors are easier to validate and replay.

**Probe/failure mode:** `workspace/reference_probe.py` independently measures
component connectivity and enclosed regions.  Task tests force each profile to
refute its intended rival.  The constructors currently modify only the first
object in complex profiles; the second object remains a canonical anchor.

## D3 — Add an exterior bounding-box zero safely

**Decision:** For `notched` and `split`, remove one corner of a 5x5 ring after
constructing the enclosed topology.  Four-neighbor connectivity keeps the hole
sealed, but the missing corner is an exterior zero inside the object's bbox.

**Rationale:** This is the smallest witness separating true enclosed-region
extraction from the canonical-fitting `all_bbox_zeros` rival.

**Rejected alternative:** Remove a side cell.  That can open the interior and
change the task rather than distinguish the rival.

**Probe/failure mode:** `self_check` rejects opened or solid objects.  The
independent probe asserts an exterior bbox zero and verifies Racket parity.

## D4 — Use a rotation-safe five-pair teaching schedule

**Decision:** Use `notched, split, notched, split, rectangle`, with four
examples and one query.

**Rationale:** A notched example refutes bounding-box fill; a split example
refutes largest-region-only; either complex profile refutes all-bbox-zeros.
Duplicating notched and split means holding out any one pair still leaves both
witness types visible.

**Alternatives considered:**

- Three demonstrations plus one query: too easy for a held-out decisive witness
  to disappear.
- A random independent profile draw: can form all-rectangle or single-witness
  lessons.
- A fixed query position only: acceptable for an ordered curriculum, but weaker
  and needlessly fragile when arbitrary rotations are affordable.

**Probes:** Task tests enumerate all five cyclic starts and all query positions.
The production census checks 300 lessons and all 1,500 pair holdouts.

**Limitation:** The schedule is periodic and deterministic in topology, although
geometry, placement, dimensions, color order, and palette vary.  This is a
teaching guarantee, not a claim of IID profile sampling.

## D5 — Keep four exact observable axes

**Decision:** Advertise only `grid_h`, `grid_w`, `palette_kind`, and
`pattern_kind`.  Reject unknown keys and wrong types; route exact values through
the generation context; expose `observe_overrides`.

**Rationale:** Every advertised control must be independently visible in the
returned grid.  Removing ambiguous aliases is safer than documenting hidden
precedence rules.

**Alternatives considered:** Retain `texture` as an alias or expose lower-level
shape dimensions.  Aliases recreate overlap; low-level dimensions create many
incompatible combinations without improving the semantic lesson.

**Probe/failure mode:** The override battery explores boundaries and legal joint
combinations.  Task tests cover all palette/profile combinations and both grid
bounds.  Unsupported axes fail loudly rather than silently falling back.

## D6 — Pin but do not edit the Racket authority

**Decision:** Add `RULE_HASH = "e13b35a51ff4"` and leave the canonical Racket
program unchanged.

**Rationale:** Independent Python and Racket outputs agreed on canonical,
notched, and split witnesses.  The defect was distributional and contractual,
not a reference-rule error.

**Probe/failure mode:** Rule smoke and authority synchronization are green; the
supported `apply` command records the executed rule and generator hashes.

## D7 — Build an independent reusable probe

**Decision:** Add `workspace/reference_probe.py` rather than reuse generator
internals in tests.

**Rationale:** A test that calls the generator's own component or hole helper
can repeat the same bug.  The probe independently implements grid validation,
components, enclosed-region extraction, packing, rivals, and axis observation.

**Alternatives considered:** Inline the logic in each test or call private shared
runner functions.  Inline duplication is hard to reuse; private runner imports
are not portable.

**Limitation:** It remains a Python mirror, not label authority.  Racket `apply`
is retained for authoritative parity checks.

## D8 — Stop after source-bound green evidence

**Decision:** Freeze the generator after 79/79 task tests, a 12/12 green battery,
a passing required-rotation gate, and the 300-lesson census.

**Rationale:** Further grammar expansion would add untested hypotheses after the
solve episode had been bound to the final generator hash.

**Remaining uncertainty:** Finite declared-rival checks do not prove universal
identifiability.  Approval and training admission remain maintainer decisions.

## Review 2026-10-24 — native pack-order parametric family

**Scope.** Production `generator.py` remains unchanged at SHA-256 `5c48db7df2d19349f48317ba6ccc18aaa4234323eb24ffd198945fc8fdb89547`. The native family lives under `workspace/parametric/` and preserves the exact canonical Racket source for `pack_order=left_to_right`.

**Nearby rule parameter.** The alternative `pack_order=hole_area_descending` first extracts each colored object's complete union of enclosed holes, computes the exact number of derived hole cells, then packs objects in descending derived area with source left-to-right order as the tie break. Inputs are setting-neutral; demonstration and query counts are independently prefix-stable over 2–6 and 1–4, with four controller-side queries and a substantive 30×30 case.

**Sequential dependency.** Step A extracts the complete enclosed-hole union for every object. The intermediate is the per-object exact hole-cell area vector. Step B consumes that vector to choose the descending-area pack order before packing; it cannot choose the order before Step A. The retained protected-Racket counterfactual substitutes hole-union bounding-box area and changes 14 final cells.

**Verification.** The reusable self-audit replayed 40 labels plus two causal programs through protected Racket, retained two finite-rival teaching examples, and found no survivor beyond the intended policy in the declared set. Native qualification passed both settings at seeds 0 and 17 with three demonstrations and four queries per job (40 protected-Racket labels). Public one-query exports passed byte, content-ID, schema, masking, and uniqueness checks. Evidence: `workspace/parametric/evidence/current/`, `workspace/parametric/evidence/manifest.json`, and packet checks `checks/4e05481a2c21/`.

**Status.** Reviewer-ready only. Exact-source owner acceptance and any training admission remain pending; finite rivals and two seeds do not prove universal identifiability.
