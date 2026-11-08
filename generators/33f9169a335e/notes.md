# Working notes: 33f9169a335e

## Current decision

Keep the approved v3.0.0 production generator and canonical rule unchanged. The
new files under `workspace/parametric/` are proposed prototypes, with no
parametric approval or training admission.

`ray_mode.py` has two episode settings: canonical `endpoint` and proposed
`trace`. Both recognize positional inverted-U witnesses, including mixed
colors. Trace writes 4 only into originally empty cells in the gap column,
continues below existing foreground, and never detects new witnesses from its
own paint. A mixed-color intersecting-U case guards that distinction.

`analogy.py` is a separate specialization inspired by public evaluation
`4c7dc4dd` demonstration 2: infer identity/complement from a complete framed
pair and apply it to the incomplete pair. The episode parameter chooses
target/reference output palette; the identity/complement operation comes from
each input. Complement with target palette is the source-backed case. Identity,
reference palette and the simpler stacked layout are proposed extensions.
This does not implement demonstration 1 or solve the whole public puzzle, and
the assignment's `relationship_verified=false` remains unchanged.

## Evidence and limits

The retained batch in `WORK/checks/parametric/run-v1/` has four episodes, each
with two demonstrations and four distinct queries. Protected Racket executed
38 pairs in nine calls, including the four canonical pairs, six U edge pairs,
and four contextual-counterfactual pairs. All 28 focused Python tests passed.
`report.json` binds exact programs, source hashes, runtime and public IDs.

The retained context witness uses `context_counterfactual(17, 5)`: only
reference panel A changes, its 8x8 foreground count remains 32, and reference
B, target C, frames and layout stay fixed. Every target output bit changes.
Thus B-only, target-only, and foreground-count-only explanations cannot explain
both outputs. This establishes contextual dependence for this witness; it is
not a proof against arbitrary rival programs.

Certificates filter the two declared settings using demonstrations only and
require surviving settings to agree on every query. They make no global
uniqueness claim. Samplers expose independent integer counts 1..8, reject
duplicate inputs, and fail explicitly after bounded attempts.

Two bounded review surfaces were checked independently: sampler count/retry
behavior and public export/lesson-certificate behavior. No concrete defect was
found within that pass. The review used source inspection and isolated
function probes; the retained focused suite and Racket receipts are the
execution evidence. Unrelated production batteries were not rerun.

## Reuse and next useful action

Run `retain.py` through the packet's `review.py run` wrapper into a fresh
output directory; its README supplies the exact command. Python authoring
labels become retained labels only after actual protected Racket execution.
Public filenames hash exact visible bytes; private settings, programs, seeds
and query labels are stored separately. The opt-in exporter does not change
existing dataset identities.

A maintainer can replay this small batch, assess whether these reasoning
variations add training value, and decide whether either proposal merits a
separate approval. Supporting the public task's line-connection relation is
future work, not part of this return.
