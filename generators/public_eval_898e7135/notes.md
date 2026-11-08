# Current public-evaluation creation: 898e7135

The reference is a general rule, not a supplied-grid lookup. Find the unique
nonzero component whose bounding rectangle has a complete same-color perimeter
and nonempty zero cavities. Infer one common integer scale by matching each
cavity to an outside component under all eight square symmetries. Assign each
cavity its matched component color and enlarge the solved board by that scale.
All two supplied demonstrations and the supplied test gold passed the initial
protected-Racket authoring preflight. Official challenge/gold files are unchanged.

`finish=assemble_only` uses reference.rkt byte-for-byte.
`finish=highlight_largest_fitted_cluster` consumes the completed board and
recolors its unique largest same-color 8-connected fitted cluster to 9.
In generated scenes, two diagonal equal-color cavities join into a six-unit
cluster; a remote three-unit occurrence of that color must stay unchanged.
Individual four-unit pieces and equally sized, differently shaped cavities
separate component selection and exact shape matching from plausible shortcuts.

The finite constructive grammar uses six cavities, independently transformed
outside pieces, full D4 transformations, random role colors, two integer scales,
rectangular templates, and true 30x30 assembled outputs. A finite two-shelf
partition enumerator randomly assigns and orders all source rectangles with
positive clearance. It replaced fixed role slots after a regression measured
only five source size-order permutations across 64 seeds. No retry exhaustion,
silent count fallback, original answer access, or cross-task module import occurs.
Two through six demos have stable prefixes. Exactly four private queries are
sampled, then shuffled using a distinct deterministic presentation RNG.

The admitted grammar requires a unique frame, unique common scale, and unique
matched color for every cavity. Conflicting colors and unsupported ambiguous
inputs are rejected by the independent Python analyzer. Racket uses discovery
order outside the admitted unique grammar. Piece matching is shape dictionary
matching, not an exact-cover inventory-consumption solver; generated duplicate
shapes have the same color and a matching source instance for every hole.
The source reference supports arbitrary matching connected shapes, while the
constructive sampler uses a deliberately finite shape vocabulary.

Evidence: WORK/checks/public_eval_898e7135/preflight and audit. The authoring tool
replays gold labels and the causal 4-vs-8-connectivity counterfactual through
protected Racket, tests declared finite rivals, verifies public-only one-query
exports, and checks private-field invariance. Passing these checks is not a
universal uniqueness theorem, native qualification, owner acceptance, or training
admission. Owner registration and native acceptance remain required.
