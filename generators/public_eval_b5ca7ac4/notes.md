# public_eval_b5ca7ac4: current authoring decision

**Reviewer-ready prototype; owner registration, native qualification and acceptance pending. Training admitted: false.**

## Rule and family
Recover complete rectangular frames with border 8 (pack left) or 2 (pack right), uniform solid interiors and a majority background. Preserve each frame's row, dimensions and payload. Parse full rectangles rather than connected components because frames may touch and an interior may use the other border color. Process each direction independently in original column order, nearest destination edge first; only intersecting row intervals create horizontal constraints.

packing_order=front_first preserves reference.rkt exactly. packing_order=top_first gives original top-row priority instead. Each placement updates the settled box extents used by subsequent boxes, so substituting raw columns changes later positions and final pixels.

## Decisions and repairs
Priority order was chosen rather than a paint-only variant. Minimum lessons include nonmonotone column ranks and different row overlaps. The new parser excludes interiors equal to the majority background: these are incidental voids, not payloads. This interpretation fits every original label but remains an explicit domain assumption for owner review.

A literal four-box regression exposed an incidental fifth frame formed around a background gap. Rejecting background-filled interiors fixes it; preserved pre-repair sources and reproduce_void.py replay a 25-cell protected-Racket difference. Public-byte hashing and native witness header integration defects were also repaired and regression-tested.

## Current evidence
The final protected authoring preflight matches all **4 supplied original labels**.
It runs both settings at seeds 17 and 43 with two demonstrations and four queries.
Fresh replay reproduces preflight.json, execution.json and original-pairs.json byte-for-byte.
These are authoring receipts, not owner qualification.

The final audit runs eight episodes (both settings, seeds 0,17,43,101),
208 protected-Racket audit evaluations, a 640-scene sampler sweep,
and 160 count/prefix requests. The audit counter excludes the additional causal
counterfactual and two independent protected replay evaluations.
The source-bound wrong-intermediate witness changes **127 cells** in its 30x30 query;
the native static witness validator and strict single-expression parser both accept it.
The exact-byte official export checker validates 16 single-query files with zero findings;
private-metadata/future-query/count invariance is separately exercised by the audit.

Each family supports independently selected 2–6 demonstrations and 1–4 queries;
controller presentation shuffles the complete four-query bank before truncation.
Only a single `challenge` is model-visible. Never expose private bundles or directory listings.
Both task suites together pass **58 tests**. The legacy `task-tests` wrapper still exits 1
with `Unknown puzzle` because these public IDs are not registered; that failure is retained,
not treated as a pass. No catalog, canonical authority or approval files were modified.

Author self-review was performed; no independent reviewer was available.
The sampler separates opposite-direction boxes into vertical bands; official tests additionally cover touching/interleaved cases. It is not a universal arbitrary-overlap solver. All 640 sweep inputs are distinct. The touching_rows_overlap rival survives top_first demonstrations and is query-equivalent on all checked queries; it is not claimed refuted. No checked demo-surviving rival changes a query.

## Evidence and next action
Final evidence is under `WORK/checks/public_eval_b5ca7ac4/preflight-final/` and
`WORK/checks/public_eval_b5ca7ac4/audit-release-complete/`. Reproduction commands are in `workspace/parametric/README.md`.
Owner: reconcile any overlapping parent return, review the inferred grammar, register source
with the literal RULE_TASK_ID, refresh the native inventory, then run unchanged native
qualification and acceptance. Do not train on these prototypes before that gate.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.
