# Review — `review-5e30c8712f4492fa`

- Source contract: `arcpuzzles-public-eval-creation-v1`; two missing public-evaluation families were assigned.
- `public_eval_e87109e9`: missing rule/generator → general protected-Racket cursor-route rule, standalone generator, and `highlight_shortest_route` sequential variant.
- `public_eval_78332cb0`: missing rule/generator → general contact-matched panel-chain rule, standalone generator, and `highlight_chain_center` sequential variant.
- Root references are new general rules; each task-local `canonical.rkt` is byte-identical to its root `reference.rkt`.
- Fresh task tests: 20/20 and 21/21 passed (`checks/*-tests-final/result.json`).
- Authoring preflight: four protected jobs per target; all 4 + 5 supplied labels matched (`checks/*/preflight/`).
- Bounded census: 256 episodes per target over seeds 0–127; no declared rivals survived (`checks/*/census-128.json`).
- Public projection: 32 one-query views, 48 private-field mutations, and eight positive controls passed (`checks/*/public-export.json`).
- Protected causal replays are `reviewer_replayed`; the counterfactuals change 60 and 9 final cells (`checks/*/causal/`).
- Remaining limit: reviewer-ready prototypes only; owner registration, unchanged native qualification, exact-source acceptance, and training admission were not performed.
- Needs attention: the final review was an author self-review; finite rivals and bounded seed coverage do not prove universal rule uniqueness.

## `public_eval_e87109e9`

The canonical rule removes a six-row instruction header and executes each color instruction from the color-8 square. A left/right bar determines the turn at the matching rectangle; later collisions bounce the square toward the farther extension. The alternative first computes all complete routed footprints and collision lists, then highlights the target belonging to the shortest target-contacting route. The retained wrong-intermediate rule chooses the first target-contacting route instead.

The generator covers cursor sizes 2–3, absent instructions, three- and four-target scenes, multiple bounce depths, varied palettes/backgrounds, 2–6 demonstrations, four shuffled queries, and exact 30×30 inputs. Seven named rivals were rejected throughout the 128-seed census.

## `public_eval_78332cb0`

The canonical rule partitions the canvas into 5×5 panels along color-6 separators, ignores blank color-7 panels, solves the unique edge-contact chain, and emits it in chain order. The alternative derives the completed chain and highlights its middle panel. The retained counterfactual highlights the middle occupied source panel before resolving the chain.

The sampler deliberately uses nonmonotonic chain colors and makes a noncentral endpoint larger than the chain center. These constructive constraints close the observed color-sort and largest-panel teaching leaks. Six named rivals were rejected throughout the 128-seed census.

## Reusable review tools

- `checks/run_census.py` replays any task-local authoring audit over a deterministic seed prefix.
- `checks/final_source_review.py` verifies exact canonical bytes, parses every task-local Racket program strictly, finds an exact 30×30 sample, and replays generator/adapter behavior from relocated copies.
