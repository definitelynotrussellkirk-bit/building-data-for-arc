# Current decisions: 57bafcdde8c3

## Approved production family

Production v3.0.0 stays unchanged: source SHA-256 `dc1725d9eca65b36824a210b2a0f78d84dcae14c457efd5c3d8e46e3790f598b`, rule `e47ef90b42c0`. Infer the modal background; recolor each color-preserving 4-connected non-background component of at least two cells to cyan, preserving singletons. Canonical records and approval identities are unchanged.

The prior repair replaced sparse planted shapes with dense 13×13 two-color fields because the canonical examples use that morphology. Production retains exact foreground-count anchors 27/33/45/52, canonical palette anchors plus nonzero-foreground counterexamples, and singleton/cluster/diagonal/edge/interior witnesses. Difficulty rotates the safe profile schedule rather than changing semantics. Broader dimensions and palettes remain distribution extensions. Historical census and approval receipts are inherited provenance; this authoring return does not rerun or supersede them.

## Accepted component adapter and retained authoring prototype

`workspace/parametric/components.py` fixes threshold `{2,3,4}` and connectivity `{4,8}` per episode. Default `(2,4)` materializes the exact canonical Racket source. Inputs use independent deterministic streams, dense 13×13 anchors and fields through 30×30; production size controls are unchanged. Demonstrations and query counts are independent. Every episode's inputs are distinct; insufficient or ambiguous batches fail explicitly.

The source-bound adapter is accepted separately in `parametric/accepted.json`; the original standalone exporter remains authoring evidence. The adapter selects matched inputs across settings, jointly distinguishes the six settings and rejects five extra production shortcuts, and requires positive action for both sampled foreground/background roles under every setting. Query palettes vary independently of shape, and query prefixes do not depend on the demo count. Four-query episodes contain 13×13, 16×20, 24×24 and 30×30 fields and answers. These larger profiles are an explicit distribution extension, not a change to production generation.

Owner checks: 24 focused tests; 264 protected Racket evaluations in qualification and another 264 in fresh acceptance; 828 at the four independent count corners across all six settings. A Python-only bounded sampler check exercised 171 episodes without failure. Seeds are 0..2^63−1, demos 2–8 and queries 1–8 independently. An intermediate adapter admitted a color-0-only shortcut: it fit both demonstrations and changed 24 query cells. The retained Racket witness motivated positive color-role coverage; it is not a production safety finding. Exact evidence is under `evidence/owner-parametric-promotion/`. Finite rivals and bounded seeds do not prove universal identifiability, sampler success or learning gain. Training admission remains false.

## Proposed public-evaluation-inspired family

Assignment source `edb79dae`, challenge SHA-256 `c9190b5e5bdd993afe9b9048180eebf462a222b6597f33d4d8da0ac950544a85`, remains `inspired_extension`, relationship unverified and training not admitted. `legend_templates.py` plus its independent Racket rule replace frame-interior square blocks with exterior templates selected by the original source color, then recolor through a directed legend. Template grouping preserves all same-color pieces after excluding arrows and frame.

Both one-step and terminal mapping fit the two original public demonstrations. Their predictions for the visible query differ in 88 cells, so the original hidden answer is not claimed. Color 8's query template contains 13+2 disconnected cells. Keep the whole template. The new family declares both mapping policies; chain-bearing demonstrations distinguish them. Generation varies template size 3–5, palette, layout, shape, arrow ordering, repeated labels and empty slots, within 30×30 inputs. Four retained episodes (seeds 17/29 × both policies) have two demonstrations and four queries each; all 24 labels were executed and replayed in Racket.

Instructions and bounded grammar: `workspace/parametric/LEGEND_TEMPLATES.md`. Nine declared rivals cover mapping depth and selected shape/template shortcuts; this is finite evidence rather than an unrestricted solver guarantee. Cyclic mappings are outside the shared grammar. Larger independent lesson distributions and learning value remain unmeasured.

## Reusable checks and next action

Public challenges use `reviewer_support.public_challenge_bytes/id`; opaque names and ordering depend only on visible examples. Keep private answers, settings, programs and certificates separate. Strict grid types reject Python bool/float aliases; export verification rejects empty or incompletely hashed inventories and stale certificates. Twenty focused tests pass (7 component, 13 legend).

Use the accepted component adapter through the standard opt-in exporter documented in `workspace/parametric/README.md`. The separate inspired legend family still needs source interpretation and its own qualification before any acceptance. Production approval, parameter acceptance and training admission remain separate. No shared executor or production source changed.
