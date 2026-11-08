# Review notes: 531e65dffc0a

## Baseline

Pinned baseline generator SHA-256: `1e23bb1c7e683034cf28ac6c354b9b3e8a9f43ef3310d8244a82d08fbb1c03bb` (`VERSION = 1.2.1`). Historical assignment metadata was used only as a lead: it mentioned a missing rule hash and required fresh defect-lint measurement. The completed before battery is the measurement of record.

Measured baseline defects:

- no `RULE_HASH` pin;
- `self_check` accepted nearly empty/all-background, singleton, short-line, solid-2x2, and full-one-color impostors;
- advertised exact overrides were ignored or lacked keyed provenance, and unknown keys were silently accepted;
- only 2/60 draws matched an exact canonical profile and hard had zero profile support in the 20-draw band check;
- no executable semantic contract;
- random prototypes could be rotationally symmetric, anchor codes could repeat, and legal stamp footprints could be clipped or overlap.

## Repair choices

- Kept the selected Racket authority byte-identical and pinned `RULE_HASH = "4acd30f1e03a"`.
- Narrowed all four public axes to the ranges that can be jointly guaranteed and observed: grid sides 10–12, anchors 2–4, prototype cells 3–5.
- Scheduled the three canonical `(height,width,palette-size)` profiles, with one 4-anchor sample per 12 ordinary samples so full-axis support does not erase canonical support.
- Grew 4-connected 3–5-cell prototypes inside a 3x3 box and rejected any with fewer than four distinct rotations.
- Scheduled distinct anchor codes so every three consecutive ordinary samples covers `2,3,4,5`.
- Backtracked over placements until every transformed footprint is in-bounds, disjoint from the source prototype and other stamps, and anchors do not collide with footprints.
- Replaced permissive validation with task-grammar validation and exact override observation.
- Added a pure-Python authority mirror, six executable rivals, ten witnesses, and `lesson_identifiable`.
- Declared `code_4_as_identity` as a canonical-compatible shortcut: the only canonical code-4 prototype is 180-symmetric, so generated asymmetric code-4 examples are necessary.

## Tests and probes

Task-local TDD evidence retains the original source and red results under `workspace/generator_before_review.py`, `checks/task-tests-red/`, and `checks/probe-tests-red/`. Final portable task tests: 94/94 passing in `checks/task-tests/`.

`workspace/distribution_probe.py` is a reusable source-to-source probe. It compares exact overrides, strict validation, rotational asymmetry, canonical-profile support, named-rival elimination, canonical-shortcut fit, rolling lessons, and all cyclic assignments of four materialized pairs to the query slot. Final output is `workspace/distribution_before_after.json`.

The shared 100-lessons-per-band census produced 300/300 unambiguous lessons, 1,200/1,200 unique inputs, no hook warnings or scoring errors, and 100/100 refutations for every declared rival in each band. The task-local cyclic probe passed 384/384 query rotations.

## Limits retained deliberately

- Exact dimensions are constrained to 10–12 rather than the old claimed 8–16 because the selected distribution is calibrated to canonical profiles and guarantees non-clipped placements.
- Anchors are distinct in ordinary data; repeated same-code anchors are lawful under the Racket rule but omitted because they add little branch evidence and weaken three-example coverage.
- Prototype size is capped at five cells in a 3x3 box; larger shapes are lawful but not needed for the identified training defects.
- Rival checks are finite and do not prove universal induction. The query-rotation probe closes one known census gap, not all possible shortcut families.
