# Working notes: 6347dcb736b5

## Review outcome

Baseline generator SHA-256:
`7f5ced9ff235b346ae87d217c830260f3bf46624dd6e0e88fc51bdf9a42f79e7`.
Final generator SHA-256:
`c62e94fcc14703261d5bbb0e2e736f1bc9009be908fc5276322f365672c99936`.
Rule hash: `6bba75bb466d`; Racket authority unchanged.

The baseline failed lint, defect lint, and override checking and had advisory
profile/semantic gates. Its public API listed controls that were ignored or
singletons, difficulty bands rejected values advertised as valid, unknown keys
were accepted, the validator admitted minimal impostors, and no generated lesson
contract addressed canonical shortcuts.

## Selected design

- Construct bounding boxes first and backtrack their placement with one-cell
  separation, then generate connected non-solid shapes touching all four bbox
  sides.
- Guarantee one >=3×3 component with an occupied strict-interior cell. This
  refutes `fill_bbox` and `outline_over_input` on every sample.
- Repeat one color across exactly two disconnected components in sample-index
  slots 1 and 2 modulo 3. Slot 0 remains distinct-color. This refutes the
  canonical-fitting `global_color_bbox` rival in every three-demo consecutive
  lesson and every query rotation of four consecutive pairs.
- Keep only three exact public controls: height 6–14, width 9–16, and 2–5
  objects. Difficulty changes weights, not validity.
- Mix palette-aware canonical profile anchors with broad draws. In repeated-color
  slots, object count is palette size rather than being confused with it.
- Validate actual grid semantics, not generator metadata.

## Retained failures that informed the repair

- Baseline battery: `checks/before/` — 7 green, 2 advisory, 3 failed.
- First TDD implementation: `checks/tdd-green-attempt1.log` — 26 passed, 3
  distribution failures because five-object cases were too rare.
- Repeated-color shortcut tests before implementation:
  `checks/tdd-repeated-color-red.log` — seven expected failures.
- First repeated-color profile gate: `checks/repeated-profile/` — easy band had
  zero exact profile support; corrected by palette-aware anchoring.
- Distinct-color semantic pass that missed the undeclared shortcut:
  `checks/intermediate-distinct-only-after/`.

## Final evidence

- Full battery: 12/12 green in `checks/after/`.
- Task tests: 36/36 in `checks/task-tests/result.json`.
- Lesson census: 300/300 lessons and 1,200/1,200 rotations without declared-rival
  ambiguity in `checks/lesson-census.json`.
- Exact global-color counterexample: `checks/shortcut-counterexample/`.
- Independent reusable geometry code: `workspace/reference_probe.py`.

## Known limits

The production manifold intentionally separates bboxes, duplicates at most one
color across two components, and favors non-solid objects with a decisive
interior witness. The finite rival census does not prove unique induction against
all possible programs. Passing this review does not itself confer catalog or
training approval.
## Current reviewer considerations

Source SHA-256: `c62e94fcc14703261d5bbb0e2e736f1bc9009be908fc5276322f365672c99936`.

# Design decisions for `6347dcb736b5`

Final generator version: `2.0.0`
Final generator SHA-256: `c62e94fcc14703261d5bbb0e2e736f1bc9009be908fc5276322f365672c99936`
Selected rule hash: `6bba75bb466d`

## D1 — Preserve the Racket authority

**Decision.** Do not change the canonical or base Racket rule. The rule is
coherent, all three canonical pairs match it, and the baseline rule-smoke and
authority-sync stages were already green.

**Alternative considered.** Alter the authority to accommodate degenerate or
ambiguous baseline outputs. Rejected: the observed defects were entirely in the
input generator, public control contract, validation, and lesson semantics.

**Probe/failure mode.** Every final canonical pair is checked by both the task's
Python mirror and an independent workspace oracle; the full battery runs Racket
rule-smoke and authority synchronization. A rule drift would fail the pin,
canonical tests, or authority checks.

## D2 — Replace random growth with constructive bounding boxes

**Decision.** Choose object bounding-box dimensions first, place those boxes by
backtracking with a one-cell gap, then draw a connected non-solid shape inside
each box that touches all four sides.

**Rationale.** The task transformation depends on per-component bboxes. A
constructive sampler can guarantee the components, separation, bbox dimensions,
and witnesses that a random walk only sometimes produces. It also makes every
advertised corner of the axis domain feasible.

**Alternatives considered.** Keep `_grow_blob` and reject bad samples, or retry
until enough components happen to fit. Rejected because the baseline silently
skipped failed blobs, making `n_blobs` inexact and leaving semantics to chance.

**Probe/failure mode.** Tests request every Cartesian corner of height, width,
and blob count in every difficulty band. `self_check` independently recomputes
components and bbox separation. Placement failure falls back only to smaller
unadvertised textures; it never changes a requested public axis.

## D3 — Public axis choices

The original rationale for the imported dead axes (`palette_kind`,
`palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`)
is not recoverable beyond the baseline comments. Four palette textures were
ignored, two enum axes had only one value, three degenerate textures occupied the
ordinary domain, and several semantic axes had no implementation/provenance.
They were removed rather than preserved as fictional controls.

| Choice | Final domain/default | Why | Rejected alternative | Probe and failure mode |
| --- | --- | --- | --- | --- |
| `grid_h` | Exact 6–14; full-domain weighted draw | Includes all canonical heights (6, 8), retains broad scale, and is feasible with 2–5 boxes. | Baseline declared 6–15 but difficulty clamped to narrower ranges; height 15 added area without a demonstrated task need. | Every min/max corner is requested under all bands; observed height and replay are asserted. |
| `grid_w` | Exact 9–16; full-domain weighted draw | Canonical widths are 9/10; extra width supports separated 5-object cases. | Baseline declared 6–15 despite no canonical width below 9 and rejected legal overrides by band. | Same corner/replay probe as height. |
| `n_blobs` | Exact 2–5; full-domain weighted draw | Multiple components are necessary to teach “each object”; 5 exercises the upper control. | A single-object degenerate and silent placement drops. | Component count is independently observed for every corner; broad tests see exactly `{2,3,4,5}` in each band. |
| Difficulty | Weighting only | Easy/medium/hard should alter frequency, not invalidate documented exact controls. | Band-specific hard clamps. | The same requested corners must work in `None`, easy, medium, and hard. |
| Colors | 1–9; one shared color in two of three slots, otherwise distinct | Preserves object color while distinguishing component identity from global color grouping. | Always-distinct colors preserve the strongest canonical shortcut; always-repeated colors create an equally artificial invariant. | Every four-pair window and all four query rotations retain a repeated-color demo. |
| Background | Always 0 | Matches canonical task and authority. | Variable background adds an unrelated inference burden. | Validator rejects out-of-range/ragged structures; independent oracle assumes documented background. |

## D4 — Guarantee an interior-erasure witness in every grid

**Decision.** The first component has a bbox at least 3×3 and includes a strict
interior source cell, while remaining non-solid.

**Rationale.** This single geometry makes two common rivals visibly wrong:
“fill the bbox” paints too much, while “outline over the source” fails to erase
the interior source cell. The witness is per-grid, so lesson assembly cannot
accidentally omit it.

**Alternative considered.** Rely on a 4×4 blob appearing in one of three demos,
as the baseline comments proposed. Rejected because the implementation never
guaranteed it and because a per-grid witness is cheap.

**Probe/failure mode.** Across 180 draws per band plus the semantic census, every
grid fires `interior_erasure`, and both rivals disagree with the oracle. A solid
rectangle or thin line is rejected by `self_check`.

## D5 — Counter the canonical-fitting global-color shortcut

**Decision.** Declare `global_color_bbox` as a canonical shortcut and semantic
rival. In sample-index slots 1 and 2 modulo 3, exactly two disconnected components
share one color; slot 0 keeps colors distinct.

**Rationale.** All three canonical examples use each nonzero color for only one
component, so “merge all cells of each color and outline one global bbox” fits
all canonical outputs. A three-slot schedule gives any three consecutive demos
at least two direct counterexamples, including every held-out-query rotation of
a four-pair lesson.

**Alternatives considered.** Random color reuse was rejected because a finite
lesson could miss it. Reuse in every sample was rejected because it would teach
an unnecessary universal color-repetition prior. A four- or longer-period
schedule was rejected because `EXAMPLES_NEEDED = 3` should be sufficient.

**Probe/failure mode.** The exact seed-91/sample-1 counterexample is checked by
Racket and differs at 14 cells. Task tests exhaust cyclic starts 0–11 in every
band and every query rotation. The 300-lesson census reports zero ambiguity
against the declared rivals.

## D6 — Canonical profiles plus broad support

**Decision.** Mix a `core` curriculum mode anchored to canonical
`(height, width, palette-size)` profiles `(6,9,3)`, `(8,9,3)`, `(8,10,4)` with a
`broad` mode over all public domains. For repeated-color slots, derive object
count from palette size by adding one, so the visible palette still matches the
anchor.

**Rationale.** The baseline had zero canonical-profile support, but blindly
pinning object count to palette size breaks when two objects share a color.
Palette-aware anchoring keeps the actual profile definition honest while still
producing repeated-component-color witnesses.

**Alternatives considered.** Only canonical sizes would overfit three examples;
only broad random draws failed the profile floor. The first repeated-color
revision used object count directly and produced zero exact easy-band hits; its
failure is retained under `checks/repeated-profile/`.

**Probe/failure mode.** The official 20-draw-per-band seeds must include at least
one exact profile. Final support is easy 6/20, medium 7/20, hard 12/20. Separate
180-draw tests require at least 16 distinct dimensions and all four blob counts
per band.

## D7 — Strengthen `self_check` to the declared manifold

**Decision.** Validate rectangular grids, 0–9 cells, dimensions, 2–5 connected
components, non-solid 2-D bboxes, one-cell bbox separation, and at most one color
shared by exactly two components. Canonical inputs remain lawful.

**Rationale.** The baseline checker only counted two nonzero cells and even
special-cased a metadata texture. That did not protect tests, semantic hooks, or
future callers from out-of-domain inputs.

**Alternative considered.** Validate only generated provenance. Rejected because
canonical examples and external probes need a content-based validator.

**Probe/failure mode.** Minimal impostors (empty, all-background, singleton,
line, solid 2×2, full one-color) are rejected. A lawful two-component same-color
case is accepted; a triple-reuse case is rejected.

## D8 — Keep a Python mirror, but never make it authority

**Decision.** Retain `rule_mirror` and independent `workspace/reference_probe.py`
for fast tests, while all decisive counterexamples and official checks use the
selected Racket program.

**Rationale.** A Python oracle makes task-local TDD practical, but importing the
generator into its own oracle would make shared mistakes invisible. The workspace
probe deliberately does not import `generator.py`.

**Probe/failure mode.** All canonical pairs must match both implementations.
The Racket `apply` receipt binds the exact counterexample output to rule hash
`6bba75bb466d` and final generator bytes.

## D9 — Determinism and replay

**Decision.** All randomness comes from `gen_ctx` keyed draws; generation returns
fresh rows and leaves Python's global RNG unchanged. `observe_overrides` exposes
the three semantic controls.

**Rationale.** Source-bound lesson census and exact override replay depend on
stable `(seed, sample_index, difficulty, overrides)` behavior.

**Probe/failure mode.** Tests compare repeated calls byte-for-byte, mutate a copy
to establish freshness, verify global RNG state, and replay 80 ordinary draws per
band using observed overrides.

## D10 — Limits retained deliberately

- Generated bboxes are separated by at least one background cell. Touching
  different-color components are not currently sampled.
- Every generated component is non-solid and every grid has an interior witness;
  canonical solid-border edge cases remain accepted by `self_check` where lawful,
  but the production distribution prioritizes teaching value.
- At most one color is duplicated, across exactly two components. More complex
  repeated-color partitions are excluded to keep the grouping witness legible.
- The source-bound census tests the declared competitors over 300 deterministic
  lessons and all 1,200 rotations. It is finite evidence, not a proof of unique
  induction against arbitrary programs.
- Training approval remains outside this review. Passing checks do not set catalog
  approval or train-safety metadata.

## 2026-10-24 — Native marker-relay parametric family

- **Canonical preservation.** `outline_scope="all_objects"` returns the selected
  canonical Racket source byte-for-byte; production `generator.py` is unchanged.
- **Alternative rule.** `outline_scope="marker_relay"` first outlines every
  component bbox, samples the unique newly painted nonzero corner adjacent to a
  color-9 marker, and then redraws only the two disconnected components carrying
  that sampled color. A second repeated-color pair is a structural distractor.
- **Teaching contract.** Inputs are matched across settings; 2–6 demonstrations
  distinguish both settings and four named shortcuts, and every episode has four
  distinct queries at 8x12, 14x18, 22x26, and substantive 30x30 scales.
- **Bounded evidence.** The retained audit passed 72 setting/count/seed jobs;
  protected Racket matched 28 retained labels; the native qualification passed
  four jobs and 40 Racket evaluations. Sixteen one-query public projections hide
  settings, programs, answers, and future queries.
- **Causal witness.** Two protected cases replay a wrong sampled color. The
  counterfactual changes 42 cells on an 8x12 query and 140 cells on the 30x30
  query, including the remote payload, so B cannot be selected from marker
  adjacency before A creates and reads the corner color.
- **Limit.** This is finite reviewer qualification, not owner acceptance,
  universal learnability, measured training gain, or training admission. Exact
  integrated bytes still require owner-side qualification, witness replay, and
  acceptance.
