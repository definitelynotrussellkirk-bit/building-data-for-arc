# Current notes: `0832c700ffb9`

## Source state

Candidate version `2.1.0`; generator SHA-256 `a7f97e5f113536579cbcc2cf6245c7ea325d34b387ca2707435070208cf2758f`; canonical rule hash `781d2d53fe4d` unchanged. The approved baseline for assignment `review-4c10bb8a426de6a4` was SHA-256 `160bcb93f94f83245ca71cc744747025542c0eaa1e99336461ee4f9029e45ac3`. The prior accepted return `review-7d079ba1796a4c49:v0001` was used as a lead, then current behavior was remeasured.

## Intended rule

Each nonzero input dot becomes the center of a clipped 3×3 block. The eight ring cells copy the color of that dot's unique same-row partner. Color-5 dots connect every same-row and same-column pair at stride two after block painting. The selected Racket program and canonical examples were not changed in this review.

## Lawful production inputs

- Grid height and width are exact observable controls in `14..18`.
- Inputs use two distinct dot colors from `{1,2,3,4,6,7,8,9}`; color 5 is output-only.
- A scene contains one or two complete, disjoint rectangles with row/column gaps of at least four. Every dot has one row and one column partner; unpaired dots are excluded because the pinned authority can emit `#f` for their rings.
- Public textures are `plain`, `same_rows`, `two_rects`, `border_rect`, and `two_rects_border`.
- Ordinary lessons repeat `two_rects`, `border_rect`, `two_rects_border` across five demonstrations plus one query. Repetition preserves border and multi-component witnesses under every single-query rotation.

## Current review changes

The only production-facing repair is strict replay-scalar validation. `seed` and `sample_index` require exact type `int`, `sample_index` must be nonnegative, and `difficulty` must be `None`, `easy`, `medium`, or `hard`. `generate` and `schedule_profile` share the validator. Six lawful replay fixtures remain byte-identical to the baseline.

A runnable **proposal**, not production integration, lives in `workspace/parametric/`. It varies `ring_partner_axis` between canonical `row` and proposed `column` once per episode while preserving object roles, 3×3 expansion, and guides. Canonical examples alone do not identify this parameter; same-row-color rectangles do. Racket-backed evidence is in `checks/parametric/ring-partner-axis-v1/` in the review return.

The strongest retained canonical shortcut is `first_rectangle_only`: it fits all five canonical pairs but differs on an ordinary emitted `two_rects` case in 44 cells. The exact witness is `counterexamples/review-4c10bb8a426de6a4/first_rectangle_only.json`, covered by a focused test. The existing schedule already refutes it.

## Final evidence

- Before battery: 11/12; only `defect_lint` failed with 48 strict-scalar warnings.
- After battery: 12/12 green; authority set unchanged.
- Portable task tests: 562 passed.
- Profile floor: 60/60 exact and envelope hits, 0 crashes.
- Rule smoke: 120/120, with 0 Python-mirror mismatches.
- Override matrix: 8,190/8,190 accepted, 0 findings/warnings, unknown key rejected.
- Lesson census: 300 lessons, 1,800 pairs/rotations, 0 ambiguity; 1,791 unique inputs.
- Parametric proposal: 116 Racket labels, 48/48 identifiable rotations.

## Limits and open status

The rectangle manifold is deliberately narrower than all aligned-dot graphs. Declared rivals and finite seed/rotation censuses do not prove universal rule identifiability. The row/column prototype has only two settings and is not approved or selected. This review makes no training-admission claim; maintainers must independently replay the returned patch and evidence.
## Current reviewer considerations

Source SHA-256: `a7f97e5f113536579cbcc2cf6245c7ea325d34b387ca2707435070208cf2758f`.

# Decisions for `0832c700ffb9`

Final candidate generator SHA-256: `a7f97e5f113536579cbcc2cf6245c7ea325d34b387ca2707435070208cf2758f`
Canonical rule hash: `781d2d53fe4d` (unchanged)
Prior lead consulted: accepted return `review-7d079ba1796a4c49:v0001`; all current claims were remeasured.

## D1 — Preserve the selected Racket rule and canonical default

**Choice.** Do not change the canonical Racket program, canonical examples, `RULE_HASH`, block expansion, guide color, or the production row-partner meaning.

**Rationale.** The baseline's only current blocker was at the Python public-call boundary. Authority sync, canonical labels, rule smoke, profile support, overrides, and teaching checks were already green. The after authority-set hash is identical to the before hash.

**Alternatives considered.** Integrate a new rule directly, change guide color, alter expansion radius, or reinterpret unpaired dots. Each would change the selected task rather than repair the measured defect.

**Probe and limit.** `checks/before/` and `checks/after/` bind the same authority set. This decision does not assert that the canonical rule is the only reasonable member of the family; P1 explores one nearby proposal separately.

## D2 — Keep the established lawful input manifold

**Choice.** Production inputs remain one or two complete two-color rectangles on 14–18 by 14–18 grids. Dots have exactly one same-row partner and one same-column partner; row/column gaps are at least four; separate 3×3 neighborhoods remain legible. Color 5 is reserved for output guides, and dot colors are two distinct values from `{1,2,3,4,6,7,8,9}`.

**Original rationale.** The prior accepted repair excluded unpaired dots because the canonical Racket search can return `#f`, and it used complete rectangles to make partner identity, clipping, multi-component behavior, and guide placement structurally checkable. That rationale remains supported by the current rule smoke and strict validator.

**Alternatives considered.** Arbitrary aligned-dot graphs are broader but can introduce multiple partners and accidental alignments; lone dots are not safely ARC-valued under the pinned authority; fixed canned scenes reduce diversity.

**Failure mode and limit.** This is intentionally narrower than every syntactically possible aligned-dot graph. Passing on this manifold does not define behavior for arbitrary partner graphs.

## D3 — Retain the public axes and deterministic lesson schedule

**Choice.** Exact public controls remain:

| Axis | Domain/default | Reason |
|---|---|---|
| `grid_h` | exact integer 14–18; periodic canonical-shape default | Keeps every ordinary draw in a measured canonical profile while allowing controlled shape variation. |
| `grid_w` | exact integer 14–18; periodic canonical-shape default | Same as height; independent exact override remains observable. |
| `texture` | `plain`, `same_rows`, `two_rects`, `border_rect`, `two_rects_border` | Each value is recoverable from the input and exposes a distinct structural teaching case. |
| ordinary profile | period three: `two_rects`, `border_rect`, `two_rects_border` | In a six-pair lesson, each profile occurs twice, preserving border and multi-component witnesses under every single-query holdout. |
| demonstrations | five | Leaves five demonstrations and one query, retaining every repeated profile under rotations. |
| `difficulty` | `None`, `easy`, `medium`, `hard` | Keys layout streams without changing task semantics. |

**Alternatives considered.** Purely random profile selection makes teaching support probabilistic. Fewer demonstrations or a nonrepeated schedule can lose the only border/multi-rectangle witness when that pair becomes the query.

**Probe and limit.** The final semantic smoke checked 72 rotations; the larger census checked 1,800. These finite checks cover the actual sampler and declared rivals, not every imaginable schedule-specific heuristic.

## D4 — Reject invalid replay scalars before coercion

**Choice.** `seed` and `sample_index` must have exact Python type `int`; booleans, floats, and numeric strings are rejected. `sample_index` must be nonnegative. `difficulty` must be exactly one of `None`, `easy`, `medium`, or `hard`. Both `generate` and `schedule_profile` use the same validator.

**Rationale.** The pinned baseline silently accepted 48 invalid probes across easy/none/hard contexts. Coercible aliases can collapse replay identities or select unsupported scheduling branches.

**Alternatives considered.** Coerce with `int(...)`, validate only inside `gen_ctx`, or accept unknown difficulty as an extra stream. Those approaches preserve the defect or create undocumented identities.

**Probe.** TDD red: 17 failures and 6 existing hash checks passing. TDD green: 23/23. Six valid calls retain fixed pre-repair output hashes, so this changes only invalid-input behavior.

**Limit.** Negative integer seeds remain valid because the established generator and RNG contract already support them; only negative `sample_index` is forbidden.

## D5 — Add a bounded row-versus-column parameter prototype, not a production variant

**Choice.** Under `workspace/parametric/`, define hidden episode parameter `ring_partner_axis` with allowed values `row` and `column`; default/canonical is `row`. Select one value once per deterministic episode. Use the same lawful inputs, 3×3 expansion, and color-5 guides for both settings.

**Rationale.** This is the smallest family extension that preserves the original object roles and relational reasoning. Every lawful rectangle supplies both a unique row and a unique column partner. Same-row-color rectangles distinguish the settings; diagonal-color canonical examples deliberately do not.

**Alternatives considered.** Parameterizing guide stride, guide color, block radius, clipping, or number of rectangles either changes more of the visual grammar, introduces trivial surface cues, or mixes rule and input-distribution parameters.

**Probe.** The default row Racket program is byte-exact canonical. Across 58 inputs and two settings, 116/116 Racket labels match the assertion mirror. Eight six-pair episodes produce 48/48 identifiable single-query rotations; a same-input witness differs in 32 cells.

**Failure mode and limit.** The proposal has only two values and depends on same-row-color teaching scenes. Canonical examples alone cannot identify the axis. It remains separate from production and carries no approval or training claim.

## D6 — Retain the `first_rectangle_only` counterexample even though the schedule already refutes it

**Choice.** Store the exact normal emitted two-rectangle input, Racket output, rival output, hashes, and replay metadata under `counterexamples/review-4c10bb8a426de6a4/`, with a focused test.

**Rationale.** It answers the assigned shortcut question with executable evidence and protects a high-value teaching property. The rival fits all four canonical demonstrations plus the canonical test because each canonical pair contains only one rectangle.

**Alternative considered.** A prose-only answer would be smaller but would not be source-bound or regression-testable. Altering the schedule was unnecessary because `two_rects` already occurs twice in every six-pair lesson.

**Probe and limit.** The retained case differs in 44 cells and is confirmed by the pinned Racket rule. It refutes this named rival, not every possible component-selection heuristic.

## D7 — Keep evidence exact but compress the oversized census

**Choice.** Preserve the complete 300-lesson JSON as deterministic gzip plus an original-path/size/SHA restoration manifest; keep the compact summary separately.

**Rationale.** The raw census is 25,608,962 bytes, leaving no room under the 25 MiB expanded return limit for the source patch, solves, audits, and required reports. Gzip reduces it to 731,850 bytes without discarding a row.

**Alternative considered.** Returning only the summary would lose exact materialized lessons and rotation outcomes. Including the raw JSON would make the return invalid.

**Limit.** Maintainers must restore it before row-level inspection; `checks/lesson-census.compressed.json` gives the exact command and hashes.

## D8 — Leave both audit targets unchanged

**Choice.** Report source-bound findings for `a1b1c1f9b042` and `8387b52c80df` but do not patch them.

**Rationale.** The assignment makes these adversarial audits, not repair targets. Their evidence is independently useful and is bound to the exact audited generator and rule hashes.

**Limit.** A1 is a concrete three-demonstration ambiguity witness, not a full schedule census. A2 establishes control/provenance defects while retaining a valid authority output; it does not challenge the Racket label itself.
