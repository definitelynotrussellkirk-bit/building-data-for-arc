# Working notes: 05ede1ccd0f1

## Current rule and binding

Version `4.0.0`; source SHA-256
`8ae178585a2dbad22de7f3673e5518cdc376358d57c8b0f093c3011680bb20f6`.
The unchanged selected Racket authority is pinned by
`RULE_HASH = "55bc14a48684"`.

Find the first full-height color-8 column. Preserve the input, then copy every
non-{0,8} cell strictly left of that divider to `(row, 2*axis-column)` when in
bounds. Sources stay. Out-of-bounds copies vanish, copied cells overwrite
existing destinations, and off-axis color-8 cells are skipped.

## Repair decisions

The prior source omitted `RULE_HASH`, exposed an override surface it could not
honor, and generated a structurally noncanonical manifold without executable
lesson rivals. The replacement uses exact observable axes:

- `grid_h`: 4..12
- `grid_w`: 6..16
- `n_cells`: 2..8
- `texture`: `plain`, `clip`, `right_content`, `eight_decoy`

Every declared combination is constructible. Unknown keys, malformed values,
and invalid sample indexes fail loudly. `source_on_right` remains a direct
negative fixture because it makes the ordinary transform identity; it is not a
public texture.

The eight-slot schedule alternates centered canonical-profile anchors with
off-center multicolor/multicomponent witnesses. Lessons use three demonstrations
and one query. Four declared competitors cover grid-center reflection,
first-color-only, first-component-only, and canonical foreground-order
shortcuts. Every cyclic single-pair holdout retains the needed witnesses.

## Evidence and limits

Focused tests pass 73/73. The final aggregate is 11/12 green; the only red stage
is the semantic smoke's unconditional warning that a declared finite schedule
must be enumerated separately. That follow-up is complete: 24/24 fixed-seed
lessons and 96/96 rotations with zero ambiguity/errors. A separate 100-per-band
census found 300/300 clean lessons and 0/1200 ambiguous rotations. Exact override
coverage accepted 34,290/34,290 calls, and canonical profile support occurs in
every band.

The finite declared/search-rival checks do not prove universal identifiability.
The training domain intentionally requires one full-height divider, at least two
left-side sources, and a nonidentity in-bounds copy. No Racket or canonical data
was changed.
## Current reviewer considerations

Source SHA-256: `8ae178585a2dbad22de7f3673e5518cdc376358d57c8b0f093c3011680bb20f6`.

# Decisions for `05ede1ccd0f1`

## D1 — Repair the curriculum, not the authority

**Measured defect.** Baseline lint failed because `RULE_HASH` was missing.
Defect lint and the override checker then showed that the declared texture/range
surface was not the surface `generate()` actually supported, and the generated
object-count/profile manifold did not overlap the canonical demonstrations.

**Decision.** Replace only the task-local Python generator and tests. Keep the
canonical Racket rule and canonical data unchanged, and pin the selected rule
with `RULE_HASH = "55bc14a48684"`.

**Rejected alternative.** Rewriting the Racket rule would have changed the
reference semantics even though all canonical examples already support the
copy-across-divider law. No generated lawful counterexample required that risk.

## D2 — State the rule at cell level

The intended transform is:

1. locate the first full-height color-8 column;
2. copy the input;
3. for every non-{0,8} cell strictly left of that column, write its color at
   `(row, 2*axis-column)` when the destination is in bounds;
4. retain every source cell and all unrelated input cells;
5. let a reflected source overwrite destination content;
6. discard out-of-bounds reflections and never copy off-axis color-8 cells.

This formulation is implemented independently in the Python diagnostic mirror
and checked against the selected Racket authority. It avoids object-shape
assumptions that the rule itself does not make.

## D3 — Use a strict, fully observable public axis contract

The final axes are `grid_h=4..12`, `grid_w=6..16`, `n_cells=2..8`, and
`texture=plain|clip|right_content|eight_decoy`. Every declared combination is
constructible; `observe_overrides()` recovers every value from pixels. The full
matrix checker accepted 34,290/34,290 calls.

**Rejected alternatives.** Keeping the earlier broader-but-infeasible ranges
would preserve a misleading contract. Treating invalid combinations as silent
fallbacks would make replay and lesson auditing unreliable. Unknown keys and
scalar coercions now fail loudly.

## D4 — Keep the identity case as a negative fixture, not a public texture

A grid with content only to the right of the divider is a useful validator
negative because the rule becomes identity and should not enter ordinary
training. It is available through `generate_degenerate(...,
"source_on_right")` and covered by tests.

An intermediate draft listed that name under `DEGENERATE_TEXTURES`; shared
defect lint interpreted the declaration as a public `generate(texture=...)`
contract and failed. The final source instead declares
`RETAINED_NEGATIVE_FIXTURES`, leaving `DEGENERATE_TEXTURES` empty and the public
texture domain truthful.

## D5 — Alternate canonical anchors with discriminating witnesses

The eight schedule slots alternate:

- centered, canonical-size, connected, single-color `plain` anchors; and
- off-center cases with multiple source colors/components, top-row sources, and
  rotating `plain`, `right_content`, `clip`, and `eight_decoy` textures.

Every cyclic four-pair lesson therefore has two witness slots. Since a lesson
uses three demonstrations and one query, every possible single-pair holdout
leaves at least one witness in the demonstrations.

**Rejected alternative.** A purely random sampler could have good marginal
frequencies yet still produce a locally ambiguous three-demo lesson. A fixed
schedule makes the teaching guarantee testable and exhaustively enumerable.

## D6 — Preserve canonical structural support in every difficulty band

Even slots reproduce canonical dimensions `(5,7)`, `(4,9)`, and `(5,11)` and
a single connected source object. Odd slots add semantically necessary variety
rather than replacing the baseline. The profile gate accepted 3/3 canonical
inputs and found exact support in all bands.

**Rejected alternative.** Sampling only off-center/multicolor stress cases
would refute shortcuts but create a different distribution restriction and
weaken continuity with the real task.

## D7 — Encode concrete rival programs, not prose diversity claims

Four executable competitors are declared:

- mirror about grid center instead of the cyan wall;
- mirror only the first source color;
- mirror only the first source component;
- mirror only when the wall is the first row-major foreground feature.

Each has a pixel-derived witness and a claim checked against the intended
output. These were selected because they either fit all canonical pairs or were
found by the semantic gate's bounded shortcut search during repair.

**Rejected alternative.** Counts such as “many colors” or “diverse shapes” do
not establish that an actual wrong rule is refuted.

## D8 — Require arbitrary single-pair query rotation

The downstream lesson policy is treated conservatively: any one of the four
labeled pairs may be the query. `lesson_identifiable()` validates every pair and
rejects a lesson whenever a declared competitor fits all remaining demos but
changes the query.

Evidence includes 12 smoke lessons with 48 rotations, all 24 fixed-seed
schedule starts with 96 rotations, and 300 random lessons with 1,200 rotations;
all are clean. This is finite evidence against the declared and bounded searched
rivals, not a proof of universal induction.

## D9 — Retain failures and distinguish a tool advisory from a semantic defect

The focused tests were written first and observed failing before implementation.
Earlier semantic runs that exposed first-color, first-component, and scan-order
shortcuts remain under `checks/`.

The final aggregate still labels `semantic_gate` failed because strict mode
turns the unconditional `declared_period_not_enumerated` follow-up warning into
exit 1. The gate itself reports no semantic error; the exact requested
period-enumeration command subsequently passed all 24 lessons and 96 rotations.
The handoff reports both facts rather than hiding the aggregate result or
removing the useful schedule declaration.

## D10 — Bound the claim

The source validator intentionally requires exactly one full-height divider,
at least two left-side source cells, and at least one in-bounds reflection. It
supports canonical inputs plus explicit lawful edge cases. It does not claim to
cover every arbitrary ARC grid accepted by the raw Racket implementation, every
random seed beyond the measured censuses, or every conceivable rival rule.

## D11 — Replay the packaged delta, not just the working tree

The final packager-generated patch was applied to a pristine extraction after
initializing Git at that extraction's exact `WORK/` root. Both apply preflight
and application exited 0; every changed path matched the authored workspace,
and the staged runtime reported the same final generator hash. The fresh copy's
portable tests passed 73/73. This catches path-root, omitted-new-file, and stale
patch failures that working-tree tests alone cannot detect.
