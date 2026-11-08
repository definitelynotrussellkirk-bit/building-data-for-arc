# Current source decision

This is a direct public-evaluation creation for 5545f144. The new general Racket
reference executes all three supplied training pairs and the public test solution.
Existing generic_waypoint_route_gen1/gen2 are inspiration-only relatives, not the
reference authority: they hardcode different motifs and assume separators.

The rule extracts the first-panel arrow motif, matches its unique rotation and
translation in the final input panel, removes those motif cells, traces nearest
aligned remaining points, and renders the same motif at the endpoint oriented to
the final leg. Matching the motif before extracting points handles the official
case where a remaining waypoint diagonally touches the cursor. A single panel is
legal. No supplied input or answer is embedded in executable source.

The episode parameter either follows the final leg (exact original reference) or
keeps the heading seen in the final input panel. Fresh generated inputs are matched
across these rules. Labels are executed through Racket, independently checked by
owner preflight and native qualification before acceptance. Current authoring
status does not imply owner registration, approval, native acceptance or training
admission.

Sampler limits: one or two input panels, 3/4/6-cell symmetric cursor motifs, four
to seven remaining route legs, unambiguous template matching and nearest steps.
The original reference also passed the supplied three/four-panel examples. Sampler
rejection is bounded; no universal completeness claim is made for arbitrary shapes,
ambiguous motif matches, equal-distance branch ties or branching routes. Finite
self-adversarial checks cover twelve shortcut rules plus the other episode rule.

Owner runtime decision: canonical authority is `ee_5545f144`; the descriptive home stays `public_eval_5545f144`. The explicit `RULE_TASK_ID` satisfies the existing reference identifier contract without changing the Racket program or sampler.
