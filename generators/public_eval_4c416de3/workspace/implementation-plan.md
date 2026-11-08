# Corner-motif family implementation plan

Goal: infer a general rule for parent 4c416de3, then provide matched-input full/outside copies with exact canonical default.
Architecture: infer black-frame corner axes, assign non-background colored marks to nearby corners, recover the maximal normalized motif, and render it at every marked corner. Independent Python claims are checked with protected Racket.
Constraints: task-local resources only; 2–6 demos; four private queries; independent presentation permutation; one substantive 30×30 query; no owner acceptance claim.

1. Write failing tests for all four supplied pairs and local corner inference; implement Python analysis and Racket reference, verifying original labels.
2. Write failing sampler/API/privacy tests; implement parameter copy_extent=full|outside, robust matched-input construction, canonical wrapper and adapter.
3. Adversarially test finite rivals, including raw translation, bbox fill, omitted frame overwrite and one-color shortcuts. Fix concrete counterexamples with regressions.
4. Run source-bound authoring preflight, protected maximum-count labels, wrong-intermediate witness and independent replay, export privacy, staged tests and relocated smoke.
5. Inventory and package evidence. Finite checks do not prove universal identifiability. Owner registration/acceptance are intentionally separate.

Design choices: 8-connected colored glyphs are assigned by nearest black-frame corner; inward axes normalize the motif. The alternate copies only frame/exterior coordinates while preserving original marks, rather than inventing a new unrelated puzzle. Ambiguous motifs are rejected by the generator grammar.
