# Working notes: c830d527a4ba

## Review outcome

Version 2.0.1 generated a color-1 object and a code region, but it did not model
the canonical transform lookup in its summary or teaching distribution.  It
also exposed overlapping ordinary/degenerate texture domains, accepted unknown
overrides, advertised controls that were not observed exactly, lacked a rule
pin and semantic contract, and had no canonical-profile support.  The baseline
battery therefore finished 7 green, 2 advisory, 3 failed.

Version 3.0.0 is a task-local rewrite.  No canonical/Racket authority changed.
The generator file used by all final checks is:

`de31633eee9869865f8a05d5dd6f75049d323badc00502d4d52448d31d44300e`

## Rule and construction

The color-1 component is cropped to a binary source template.  The bbox of
colors 2–5 is cropped as the code grid, retaining internal zeros.  Code values
select both output color and transform: 2 identity, 3 clockwise quarter-turn,
4 half-turn, and 5 horizontal reflection.  A zero code emits a blank tile with
the untransformed source dimensions.  Tiles and tile rows use the canonical
one-cell gaps and floor-centering convention.

Generated source shapes are exhaustively enumerated for 2x2, 2x3, 3x2, and
3x3 bboxes, then filtered to be 4-connected, to touch every bbox edge, and to
produce four distinct transformed shapes.  This prevents transform labels from
collapsing on symmetric templates and makes exact template bbox overrides
observable.

## Curriculum and axes

The four scheduled profiles repeat by `sample_index % 4`:

1. `canonical_left`
2. `canonical_right`
3. `gapped_left`
4. `gapped_right`

`EXAMPLES_NEEDED = 3`; every cyclic three-example window contains both template
sides and at least one gapped code bbox.  Every ordinary example contains codes
2, 3, 4, and 5.  Canonical profiles default to 6x9 and gapped profiles to 6x8,
providing both canonical-sized support and two ordinary canvas shapes.

Exact axes are `grid_h` 6..12, `grid_w` 8..14, `template_h`/`template_w` 2..3,
`code_h`/`code_w` 2..3, and `template_side` left/right.  Every declared
cross-product fits the minimum 6x8 canvas; unknown keys and out-of-range values
fail loudly.

## Semantic contract

The Python `rule_mirror` is independent of the selected Racket execution path
and matched it on all 120 final smoke draws.  The contract declares witnesses
for transform lookup, source-side invariance, and code-gap preservation.  It
also declares four lesson rivals: recolor-without-transforms, swapped 3/5
transforms, template-must-be-left, and drop-code-gaps.  The latter two fit all
five canonical pairs and therefore require generated counterexamples.

`lesson_identifiable` validates every pair against the mirror and rejects a
lesson when a declared rival fits all demonstrations but differs on the query.
The deterministic profile schedule gives that guarantee for every tested cyclic
start rather than relying on marginal witness frequency.

## Test-driven failures retained

- `checks/task-tests-red2/result.json`: initial contract tests, 7 failed / 1
  passed against version 2.0.1.
- `checks/task-tests-override-red/result.json`: 3 failures exposed catalog shapes
  that did not touch their requested top/left bbox edges.  The catalog now
  requires both minimum and maximum row/column edges.
- `checks/task-tests-canvas-red/result.json`: 1 failure exposed a shape-locked
  ordinary 6x9 distribution.  Gapped profiles now default to 6x8.

## Final evidence

- Battery: `checks/after-final/checks/c830d527a4ba_after_battery_summary.json`
  — 12/12 green, no advisories or failures.
- Focused tests: `checks/task-tests-final/result.json` — 12/12 passed.
- Override matrix:
  `checks/after-final/checks/c830d527a4ba_after_override_results.json` —
  23,040/23,040 accepted draws, zero findings/warnings, unknown key rejected.
- Semantic gate:
  `checks/after-final/checks/c830d527a4ba_after_semantic_gate.json` — 151/600
  strict-canonical hits, all witnesses and all 12 sampled lessons passed.
- Lesson census: `checks/lesson-census-final.json` — 300/300 lessons,
  1,200 query rotations, zero declared-rival ambiguities, 1,200 unique inputs.

Finite declared-rival checks do not prove universal rule identifiability.  The
ordinary distribution intentionally fixes the default height at six, restricts
small source/code bboxes to 2..3, and includes all four transform codes in every
example; these choices favor compact, explicit teaching over the widest possible
input support.
## Current reviewer considerations

Source SHA-256: `de31633eee9869865f8a05d5dd6f75049d323badc00502d4d52448d31d44300e`.

# Decisions: c830d527a4ba

| ID | Choice | Rationale and probe | Alternatives rejected | Limits / failure mode |
|---|---|---|---|---|
| D1 | Keep the selected canonical/Racket authority unchanged and pin `RULE_HASH = 0b137f4534ae`. | All five canonical pairs and 120 generated draws agree with an independently written Python mirror; authority sync and execution parity pass. | Rewriting the rule to match the old “recolor only” summary would change the task and contradict canonical outputs. | The archival divergent rule text remains outside the selected authority; the battery labels it archival only. |
| D2 | Replace version 2.0.1 rather than patch its random polyomino/gallery-style construction. | Baseline had no canonical-profile hits, no transform-aware contract, dead/overlapping texture controls, and thousands of override findings. | Retaining `tmpl_size`, `palette_kind`, `density`, and negative `texture` values would preserve dishonest or nonlawful axes. | This is a task-local rewrite, so downstream consumers depending on obsolete axis names must use the new declared contract. |
| D3 | Declare only seven exact observable axes: canvas height/width, template height/width, code height/width, and template side. | `observe_overrides` can reconstruct every value from the returned grid; the full 23,040-draw matrix passes. | A free-form “texture” axis or separate hidden position-bias controls were not retained because they are not independently observable. | Layout offsets and code values remain stochastic internal variation, not exact public controls. |
| D4 | Use a four-profile deterministic schedule with `EXAMPLES_NEEDED = 3`. | Every three-slot cyclic window contains left and right templates and at least one gap; tests cover starts 0..11 in every band and the 300-lesson census rotates every query. | Independent random profile draws could leave an entire lesson compatible with “always left” or “drop gaps.” Two demonstrations cannot guarantee all three teaching properties. | The schedule itself is predictable; it is intended curriculum structure, not a claim of i.i.d. sampling. |
| D5 | Enumerate connected bbox-filling 2x2..3x3 source shapes and require four distinct coded transforms. | Symmetric templates make transform colors observationally equivalent. The catalog regression caught nominal bboxes that failed to touch top/left edges. | Arbitrary random walks were rejected because they can shrink observed bboxes and produce transform symmetries. Fixed hand-written shapes were rejected as too small a bank. | Small bboxes favor compact lessons; larger source shapes are outside the ordinary distribution. |
| D6 | Include all codes 2, 3, 4, and 5 in every ordinary code bbox; gapped profiles add one zero without losing bbox edges or any transform code. | Each individual example then witnesses the true transform lookup, while lesson scheduling handles side/gap invariance. | Allowing missing transform codes would require a more complex cross-example coverage scheduler and could leave a query code unseen. | This is more explicit than some canonical examples and may teach a regular “all codes present” prior. |
| D7 | Anchor ordinary inputs to canonical 6-row canvases, using 6x9 for canonical profiles and 6x8 for gapped profiles. | The profile gate now has exact support in all bands; the second width fixes the interim shape-locked diagnostic (`checks/task-tests-canvas-red/result.json`). | A single 6x9 default passed correctness but reduced observable input-shape support. Wide random default canvases reproduced the baseline’s canonical-support failure. | Default height remains fixed; wider height/width support is exercised through exact overrides rather than ordinary draws. |
| D8 | Add an independent Python rule mirror, structural parser/validator, and semantic witnesses/rivals. | This enables parity checks, output validation, canonical-shortcut tests, and lesson-level ambiguity checks without importing private Racket helpers. | A self-check that only asserts “some 1 and some code exist” was too weak; marginal diversity alone cannot show that lessons teach the rule. | The declared rival set is finite. A clean census is evidence against those plausible shortcuts, not a universal uniqueness proof. |
| D9 | Reject unknown overrides and invalid difficulty/axis values immediately. | Silent acceptance was directly reproduced in the baseline and prevents reliable data provenance. | Ignoring extra keys for forward compatibility was rejected because misspellings silently corrupt experiments. | Callers must update obsolete axis names rather than receiving best-effort behavior. |
| D10 | Preserve TDD failures and the interim solve under their original source hashes. | The bbox and one-shape failures materially changed the final design; the old solve is not evidence for later bytes. | Deleting failures or copying the old solve into `solve/` would erase provenance. | Retained evidence increases return size, so checks are bundled by the packager. |

## Reusable probes

The task-local regression suite is
`repo/generators/c830d527a4ba/tests/test_generator_c830d527a4ba.py`.
It is the reusable probe for canonical parity, cyclic lesson support, exact axes,
shortcut counterexamples, bbox realization, validator power, diversity,
determinism, fresh returns, and global RNG purity.

The generator also exports `rule_mirror`, `observe_overrides`,
`strict_canonical_like`, `SEMANTIC_WITNESSES`, `LESSON_COMPETITORS`,
`CANONICAL_SHORTCUTS`, and `lesson_identifiable` for shared battery/census tools.
