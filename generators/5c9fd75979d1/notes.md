# Working notes: 5c9fd75979d1

## Current parametric design

The separate native adapter varies the strict component bounding-box-area cutoff
over 2, 4, and 8. Cutoff 2 preserves the exact canonical Racket source. Production
generator and canonical authority are unchanged. This extends the input grammar
to variable noisy mosaics, sparse fragments, and substantial 30x30 scenes.

Filtering happens before partition inference: retained colored bounding boxes
determine row/column boundaries, output dimensions, and reflected slot indices.
The causal comparison uses boundaries from all components while painting only
the correctly retained boxes. This is an input-dependent extraction/partition
dependency, not an iterative simulation claim.

Matched input streams are independent of rule setting and requested counts.
Support is 2–6 demonstrations (ordinary default 3) and 1–4 distinct queries.
The first two construction demonstrations include exact-cutoff objects and
sparse bbox-6/4-cell and bbox-9/5-cell components, separating area from pixel
count for cutoffs 4 and 8. For cutoff 2, those two statistics are equivalent on
4-connected components; their agreement is not claimed as independent evidence.

Measured-component review found a rotated bbox-8 fragment could contact a core
tile of the same color. A zero-row gap now prevents that merge; seeds 0–15 in
the first two demos retain the intended independent component statistics.

The task's old tests used a task-relative data root and required archival raw,
annotated target, and canonical program hashes to be identical. Portable root
resolution now finds the staged data. The canonical test checks the ledger,
grounded program and generator hash; separate archival hashes protect the
unchanged historical texts without asserting canonical equivalence. The Racket
test likewise recognizes the staged runtime's execution layout.

Owner acceptance of the exact integrated bytes remains the handoff boundary.
Use the task-local README for commands and the existing results/evidence records
for executed checks. No training admission is claimed.
