# Proposed conflict-policy family

This opt-in prototype preserves ARC training task d47aa2ff's aligned two-panel comparison. A full-height gray separator divides equal-width panels. Left-only cells become 2, right-only cells become 1, equal overlaps retain their shared color, and empty cells remain 0.

One episode-fixed parameter, conflict_policy, controls unequal occupied overlaps:

| Value | Conflict output |
| --- | --- |
| left (canonical default) | Left color |
| right | Right color |
| erase | 0 |

The left program is byte-for-byte the registered canonical program. The other programs add only the conflict branch. Canonical production sampling and authority are separate from this proposed family.

## Generate a comparison batch

From the outer review folder, after installing the declared Python runtime dependencies:

~~~sh
python review.py setup
python review.py run python generators/625b40fb6218/workspace/parametric/prototype.py \
  --seed 17 --input-seed 47 --policy all --demos 2 --queries 4 \
  --out ../checks/parametric/my-comparison
~~~

Use a new output directory. The command generates all three policies on the same ordered inputs, giving three complete episodes and four distinct queries per episode. Every saved label is executed through protected Racket and reexecuted before export. Use --policy left, right, or erase for one setting.

API: generate_episode(seed, policy="left", input_seed=None, n_demos=2, n_queries=4, labeler=None).
Demonstrations support exact integer counts 2..8; queries independently support 1..16. Seeds are exact integers 0..2**64-1. Booleans and floats are rejected. The input sampler rejects duplicates across all pairs and fails visibly if its bounded attempt budget is exhausted.

## Teaching construction

Two demonstrations use disjoint three-color subsets of the six legal foreground colors. Each includes a directed cycle of three unequal overlaps, along with both exclusive branches and equal overlaps. Every foreground color therefore appears on both sides of a conflict before any query. Extra demonstrations and all queries use the canonical input sampler.

The certificate fits 14 named candidates using demonstration labels only: the three policies, six favorite-color overrides, minimum/maximum color priority, swapped exclusive colors, and copies of either whole panel. It then checks each query input. A surviving rival matters only if it changes that query's prediction. Query answers are not accepted by the certificate API.

This finite family check does not prove unique induction over arbitrary programs. Two demonstrations are required by the supported sampler; the generic certificate can separately describe underidentified or query-equivalent examples.

## Public and private data

Give a model only public/. Each filename is the SHA-256 of the exact visible JSON bytes written. Public files contain demonstration input/output pairs and query inputs only. Public IDs and filenames depend on neither hidden settings, seeds, reference code, query answers nor setting order. Batches are sorted by public ID and reject duplicate visible payloads.

private/ contains the episode-fixed settings, programs and hashes, answers, source/runtime identity, and certificates. The private report is also authoring material.

verify_episode reexecutes labels, recomputes certificates, rejects duplicate inputs, checks exact integer grids and counts, and verifies the schema, original-task lineage, source/program hashes and stable live-runtime identity. Runtime paths may change on relocation; executable, prelude, bridge, boot-script and policy hashes plus security claims must agree.

Focused tests:

~~~sh
python review.py run python -m pytest generators/625b40fb6218/tests/test_parametric.py -q
~~~

This prototype is not registered in the production parametric API, approved for variants, or admitted to training. Owner qualification remains a separate action.
