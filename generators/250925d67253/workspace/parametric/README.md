# Native centroid-directed two-hop routing

Current native parameter: `route_policy = one_hop | two_hop`. `one_hop` loads
`rules/identity.rkt` unchanged from the selected canonical authority. The old
`destination_frame=identity|transpose` prototype and its tests remain available
as historical proposed authoring work, not as this native contract.

## Design and choices
A computes the arithmetic marker centroid in every original 5x5 panel and builds
the source-to-destination permutation p. B in the alternate setting follows the
edge again, placing original panel s at p[p[s]]. The intermediate is the full
input-derived p; the second address must be read from the original panel at
p[s], not from the already rearranged output. Applying the canonical transformer
twice is idempotent and is an explicit wrong-intermediate regression. A fixed
coordinate transpose was retained as a rival rather than counted as a new causal
composition. No production generator or default rule bytes were changed.

## Native API and grammar
`adapter.py` exports `program(settings)` and `generate(seed, settings, demos,
queries)`. Exact integer counts 2..6 and 1..4 are independent; a maximal private
lesson has six demo candidates and four novel queries. Every smaller request is
a prefix, including across demo-count changes. Input RNG is setting-neutral.
`native.public_turn(episode, index)` returns a detached copy with demonstrations
and exactly one query input. Never give a model the private controller episode,
program, settings, seed, directory listing, future queries or query count.

The exact law fixes nine 5x5 panels, separated by rows/columns 0,6,12,18. Its
only lawful size is 19x19. A 30x30 canvas would add undefined panel addresses;
padding is not a valid stress test. Each generated input has 225 nonzero panel
cells spread over all nine panels and all quadrants. The outer boundary is
necessarily zero. Sampling varies non-affine 9-cycles/mixed fixed points, sparse
and dense asymmetric marker motifs, and low/high palettes. The finite inherited
motif bank is a real limit: this work does not claim procedural shape diversity.

## Reusable bounded audit
From the outer packet folder (use the already checked Python interpreter):

```sh
python3 review.py run python3 generators/250925d67253/workspace/parametric/audit.py --seeds 20 --out ../checks/250925d67253/audit-new
python3 review.py task-tests 250925d67253 --phase after --out ../checks/250925d67253/tests-new
```

`audit.py` tests every supported count combination, deterministic matched inputs,
query/demo prefix stability, exact integer grids, distinct inputs, private-field
invariance, demonstration-only finite rival rejection, and standalone hashed
single-query exports. It executes all seven setting/rival programs on two retained
3-demo/4-query lessons through protected Racket and checks independent Python
predictions. Rival execution failures fail the audit; they never count as
elimination. Outputs include controller-private examples and separate public/
views. The finite rival bank is: one/two hops, three hops, inverse direction,
transposed one/two-hop destination, and unchanged source order.

## Current evidence and handoff
`checks/250925d67253/audit/report.json`: 800 count/setting requests, 5,200 pair
instances across prefixes (200 distinct input grids), 400 matched comparisons,
2,000 single-query projections, 98 protected evaluations; no findings on 20 seeds.
`checks/250925d67253/tests-final/result.json`: all 71 changed-target tests pass.
The initial missing-feature tests failed, then passed with the implementation.
The native manifest binds exact current sources and compact authoring evidence.
Qualification and the protected wrong-intermediate witness are separate receipts.
Owner exact-source acceptance and training admission are NOT performed here.
Final review was an author self-review, not an independent review. Finite tests
and authored rivals do not prove universal identifiability or learning benefit.
