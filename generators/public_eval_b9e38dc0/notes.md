# Public creation notes: b9e38dc0

## Rule and domain

Infer the unique modal background and uniquely next-most-frequent wall color. The wall is one eight-connected component with two degree-one tips; the dominant axis of their summed outward tangents identifies flow. Normalize downward, continue each terminal staircase at its observed stride and phase, and recover the interior band. Its unique earliest foreign color is the dye. Other interior colors are blockers; outside colors, including those behind the cap or before the band reaches their column, do not block.

The episode parameter is `obstacle_mode: opaque | transparent`, default opaque. Opaque mode uses the first interior blocker in each normalized column to cast a parallel forward shadow. Transparent mode fills background behind blockers. Both preserve every original colored pixel and restore the input orientation. The derived frontier vector is the intermediate consumed by opaque rendering; transparent mode deliberately ignores it.

Inputs are exact integer ARC rectangles, axes 1..30, colors 0..9. The rear cap is contiguous and at least three cells wide. Subsequent rows have contiguous side-wall runs until each tip, then virtual boundaries; their interior stays nonempty and four-connected. A complete terminal run must equal its preceding inward run, and both sides share a stride. Partial terminal runs are excluded. Clipped unequal tips, bent reservoirs and collars remain supported. Python validates this grammar; Racket assumes lawful inputs.

## Construction and binding

Ten finite profiles supply six demos and four novel queries with seeded geometry choices, palette permutations and global D4 transforms. Required demos differ in background, wall and dye colors and in flow direction. Queries are shuffled before prefix selection; no retries or answer lookup occur. Strides 1, 2 and 3 are represented. Across the design check, the two 30×30 profiles have wall spans of 19–20 rows, 49–56 wall cells, 253–289 interior cells, seven blockers and 6–8 continuation rows.

Counts are 2..6 demos and 1..4 queries; ordinary defaults are 3/4 and `qualification_demos` is the minimum 2. Seeds are exact integers in 0..2**63-1. Root generator declares `RULE_TASK_ID = 'ee_b9e38dc0'`. Reference and adjacent canonical resource are byte-identical; native reads the adjacent file. Canonical SHA256 is `6640d158c4e626dfde23389dd91183f001b5e207780a83a1fb956f86dfebde77`; normalized rule hash is `2819124fd538`.

## Completed evidence and retained repairs

Unless prefixed by `checks/`, paths below are relative to `checks/public_eval_b9e38dc0/`.

- `native-complete-v2.xml` and `audit-literals-v3.xml`: 78 native plus 82 independent audit tests passed. `sampler-v2.json`: 96/96 requests, zero failures, 160 distinct inputs, 64 query inputs and 32 distinct 30×30 inputs. Sampler structure alone does not certify protected labels.
- `design-scenes-v2.json`: 160 scene checks passed against independent flood geometry and production Python in both modes. Retained v1 exposed a side-decoy control sharing a column with a real later blocker. Repositioned blocker groups leave that decoy's future band column unblocked. `protected-rule-probe-v1.json` passed eight protected evaluations on all four official pairs in both modes, matching independent outputs and every canonical gold label.
- `learned-flow-hole-v1/report.json`: six protected calls confirm the old seed 1 hole: two demos sharing normalization turn 3 admit a fixed-flow rival that fails query 0. Old source/runtime and `orientation-diversity-red.xml` are retained. The repaired sampler guarantees distinct flow directions in the required pair. Earlier sampler/test and teaching-v1 evidence remain historical.
- `teaching-v2/private/audit.json`: all 64 labels passed; 156 fits produced 129 refutations and 27 survivors: 6 intended plus 21 proven transparent-mode aliases. All 108 survivor query scores agree. The audit used 430 protected evaluations across 484 requests; sources/runtime stayed unchanged. These aliases are retained honestly rather than counted as distinct learned behavior.
- `preflight/preflight.json`: authoring preflight passed. `causal-observations.json`: four protected measurements. Two cases were constructed with four evaluations and replayed with four in `causal/replay.json`, status `reviewer_replayed`. Only frontiers change to unblocked height sentinels; input, opaque flag, geometry, dye and the complete downstream painting/orientation code stay unchanged.
- `preview-verify.json`: 16 views across four episodes verified. Combined `checks/first-turn/report.json` passed 32 views, 8 first turns, 48 hidden-data invariance mutations and 8 positive controls. These projection/privacy checks do not rerun Racket.
- Reusable `checks/tools/probe_teaching_attributes.py` has eight passing tests in `checks/tools/teaching-attributes-green.xml`. The repaired `teaching-attributes.json` pilot covers six episodes/36 inputs, with zero flags for background, wall, dye and flow facts. This input-only attention screen is separate from semantic teaching verification.

Evidence is finite over named profiles, seeds, rivals and two causal cases, not exhaustive geometry coverage or proof against all rules. No production, catalog, runtime or training state is changed. Owner registration, source review, native qualification at the declared minimum and acceptance remain pending. Authoring preflight is not owner qualification or admission.

## Current repeated-parent reconciliation

Preserve exact opaque/transparent rules and all incumbent geometry. The incoming native family is byte-identical to current; retain it as duplicate evidence, not a new semantic setting or independent constructor. Four private queries now shuffle consistently. Current evidence resides in evidence/repeat-eighth-union. Private native acceptance and root publication are separate.
