# Current authoring decision
The parent deletes nonmatching pixels of each nonbackground color after inferring
its maximum-support vertical reflection axis. Background is the most frequent
color. Score ties select the smaller doubled column; this matters for supplied
test 0's green object. All colors are grouped, not split by connectivity.

Build: `repair_mode=trim` reproduces the parent; `complete` retains the original
object and adds its missing reflected partners. Both consume the inferred axes.
A wrong-intermediate witness replaces these axes with bounding-box midpoints.
Use varied backgrounds, both integer/half-cell axes, multiple separated objects,
asymmetric protrusions and a deliberate tied-axis branch. Four queries remain
private and independently shuffled at presentation. Inputs are setting-neutral.

Implementation checks: first pin all four official labels and the tie; implement
standalone sampler and matching Racket programs; test count/type/relocation
boundaries; audit plausible rival rules; run protected authoring preflight;
export public views and replay the source-bound causal counterfactual.
The workspace is an isolated extracted packet, not a git worktree. Source edits
stay in this task home; no shared catalog edits or owner acceptance are claimed.

## Verified handoff and limits
- Exact reference: all 2 original train and 2 supplied test labels reproduce in protected Racket.
- 21 task-local tests pass; byte-identical standalone/native sampler copies are enforced.
- The 32-seed audit covers 192 lessons / 1,472 pairs and 11 named Python rivals; every rival is rejected by the visible demonstrations.
- Authoring preflight passes both settings on seeds 17 and 43, two demos and four queries. Extra protected parity covers all 40 pairs at six demos on seeds 0 and 31.
- A 30x30 complete-setting witness replacing inferred axes by bbox midpoints changes 74 cells; fresh protected replay agrees.
- Sixteen one-query exports use independently shuffled query order and visible-byte hashes. Private fields/future queries do not alter first-turn serialization.
- The trim rule groups each color globally. Completion clips outside the canvas; ascending-color painting means higher colors win any added overlap. The sampler varies backgrounds, even/odd axes, geometry and positions; a deliberately tied support case teaches the leftmost tie-break.
- Finite rivals and seeds are not universal uniqueness/total-correctness evidence. This parent is not registered or owner-qualified; acceptance and training admission are not claimed.
- All evidence is under checks/public_eval_8e5c0c38/. Owner: reconcile source collisions, register this exact parent/reference pair, refresh native inventory and run native qualification/acceptance.
