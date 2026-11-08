# Working notes: `b19deac47327`

## Intended selected rule

Exactly one opposite border pair is solid in two distinct colors. Each color-1 marker copies the matching border color into the adjacent background cell in the direction of that border. For horizontal borders, markers in the first/top half project upward and markers in the second/bottom half project downward. Vertical borders use the analogous left/right rule. On an odd projection axis, the exact middle index belongs to the first/top-left side because the authority tests `2 * axis < extent`.

Selected rule pin: `RULE_HASH = 2b2e46dd36cc`. Generator version: `2.0.0`. The canonical Racket authority was not changed in this review.

## Current lesson contract

A lesson uses three ordered demonstrations and one query from a deterministic four-slot schedule:

1. `cross_horizontal`
2. `tie_vertical`
3. `cross_vertical`
4. `tie_horizontal`

The profiles jointly teach both orientations, the odd-axis tie, canonically unseen orthogonal edges, two-sided projection, and shape/orientation crossing. `strict_canonical_like`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable` are the executable contract.

## 2026-10-22 repair

The prior selected source accepted invalid scalar call arguments. `_validate_call_arguments` now rejects non-integer seeds, non-integer sample indices, booleans, and negative sample indices before scheduling.

The previous default schedule used only heights 12 and 13. `tie_horizontal.grid_h` changed from 13 to 15, widening the default height envelope while preserving its semantic witness, profile order, and rule.

Final selected generator SHA-256:
`66a3c56f61986c75dc40053dce167a0b6f0c513892a78de98ba521379d7809ac`.

## Final selected evidence

- Strict enumerated after battery: 12/12 green.
- Portable selected-task tests: 50/50 green.
- Standalone lint: pass.
- Profile floor: exact canonical hits 9/20 easy, 11/20 medium, 8/20 hard; canonical-envelope hits 60/60.
- Semantic census: 600/600 strict; 12/12 production lessons; 0/48 ambiguous smoke-test rotations.
- Larger lesson census: 300/300 materialized, 1,200 pairs and unique inputs, 0 production ambiguities, 0/1,200 rotation ambiguities against declared rivals.

The ordinary after command without explicit schedule enumeration is retained as an 11/12 intermediate failure. The unchanged source passed when the declared period was explicitly enumerated.

## Parametric proposal, not selected behavior

`workspace/parametric/` contains a runnable `projection_span ∈ {1,2}` prototype. Span 1 is the canonical/default behavior. Span 2 paints two consecutive cells toward the same matching border. The setting is selected once per episode and held fixed across three demonstrations and one query.

Evidence: span 1 matches all 4 canonical pairs; both settings’ complete episodes are identifiable; all 8 possible query rotations are identifiable against the opposite-span rival. Span 2 requires two clear ray cells and remains a separate proposal pending approval.

## Known limits

All identifiability results are finite and cover declared rivals only. The four-profile schedule is curated rather than uniformly sampling every legal override combination. Exact overrides expose the broader domain, but no claim is made that all possible learner shortcuts are eliminated or that this review itself grants training approval.
