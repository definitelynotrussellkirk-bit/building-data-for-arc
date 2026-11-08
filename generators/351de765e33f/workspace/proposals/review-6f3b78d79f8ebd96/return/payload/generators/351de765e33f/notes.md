# Working notes: 351de765e33f

## Current rule and authority

Version 3.1.0 keeps the canonical Racket authority unchanged (`RULE_HASH=f074243a0544`).
The rule finds same-color 4-connected nonzero components, sorts by size descending
and then top-left reading order, and recolors rank two cyan (8).

## Repaired defects

- Version 3.0.0 imposed a one-cell 8-neighbor moat that is absent from the rule and
  rejected all three canonical inputs. Cross-color diagonal and edge contacts are
  now lawful and intentionally generated.
- The old medium lesson prefix let the second-largest-distinct-size rival survive
  all five demonstrations and first disagree in a query. The declared period-eight
  profile sequence places `tie_largest_four` and `all_equal_five` four positions
  apart, so every cyclic five-demonstration window distinguishes that rival.
- Edge-contact witnesses occur at least every three schedule positions (under a
  seed-dependent cyclic shift), so every five-demo window distinguishes a
  colorblind 4-connected grouping rival. Diagonal witnesses separately exercise
  4-vs-8 connectivity.
- Calls now reject nonliteral/negative seed and sample index values, invalid
  difficulty values, unknown controls, and invalid `scene_profile` values.

## Current distribution decisions

The exact observable `scene_profile` axis remains the only production override.
All eight linked size signatures appear once per declared period in every band.
Default public-profile draws use their canonical dimensions (8x9, 8x9, 9x10),
while colors, placements, shapes, contacts, and larger-profile dimensions vary.
Distinct input colors and reserved output cyan keep object identity unambiguous.

## Executable semantic contract

`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and
`SEMANTIC_WITNESSES` expose pure deterministic rivals for distinct-size ranking
and colorblind connectivity. `strict_canonical_like` aliases `self_check`, and
`LESSON_SCHEDULE_PERIOD=8` supports exhaustive schedule replay.

## Parametric assessment

A proposed task-local prototype varies `target_rank` over `{1, 2}` once per
episode. Rank two is the canonical default; rank one is a meaningful nearby
control. It remains under `workspace/parametric/` and is not a production axis.
Exact Racket programs and complete episodes are materialized there. Direct Racket
execution was not repeated after the oversized packet runtime was lost, so that
prototype evidence is bounded to independent Python parity plus retained source.

## Verification and limits

The task-local suite has 50 passing tests. `workspace/verify_repair.py` loads the
source directly and checks 4,096 generated draws against an independent component
oracle, all cyclic five-demo windows, strict calls, overrides, rivals, canonical
acceptance, determinism, and the prototype receipt. The official packet audit draw
and post-reset Racket battery were not reconstructed; no target IDs or outcomes
were invented.
