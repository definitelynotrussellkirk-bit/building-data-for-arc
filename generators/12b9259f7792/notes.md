# Working notes: 12b9259f7792

## Current decision

The canonical rule is sound and remains byte-for-byte unchanged: each gray component is recolored by the uniquely nearest colored marker under minimum Manhattan cell distance. The base generator was not honest about its published controls, so the generator was repaired before building the family. Version 2.1.0 now strictly validates override names and realizes exact dimensions, blob count, distinct marker-color count, palette aliases, position bias, and density. `self_check` now rejects tied nearest-marker assignments.

## Native parametric family

- `all_nearest`: the exact 573-byte canonical Racket program.
- `dominant_assignment`: first perform the canonical nearest-marker assignment, total assigned blob area by marker color, then retain only the blobs assigned to the unique largest total while preserving all markers.

The second setting is a genuine input-dependent `A -> assigned-area totals -> B` rule. The protected witness uses a `skip_a` counterfactual and produces a different final grid. The family supports 2–6 demonstrations and 1–4 query prefixes while retaining four distinct private queries. Query 4 is a substantive lawful 30×30 scene; the teaching bank also distinguishes Manhattan from Euclidean distance and aggregate area from largest-single-blob shortcuts.

## Repairs made during self-review

The first construction path was too expensive under repeated prefix generation. The scene builder is now bounded and memoized, returning fresh copies so repeated prefixes are deterministic without sharing mutable grids. Focused tests cover cache behavior, count boundaries, exact canonical parity, cross-setting input identity, stress size/content, and all declared rivals.

## Retained evidence

- Focused task tests: `checks/12b9259f7792-task-tests/result.json` — 24/24 passed.
- Bounded adversarial audit: `checks/12b9259f7792/self-audit.json` — 192 cases, 1,472 labeled pairs, 576 rival checks, 32 causal checks, zero failures.
- Base-control audit: `checks/base-control-audit.json` — 128 exact-control scenarios, zero failures for this target.
- Protected authoring preflight: `checks/12b9259f7792/qualification/qualification.json` and sibling `execution.json` — both settings, seeds 0 and 17, 32 protected Racket evaluations.
- Source-bound causal witness: `checks/12b9259f7792/causal/witness.json`; protected replay: `checks/12b9259f7792/causal/replay.json`.
- Sequential public projection: 16 verified single-query views and 24 first-turn invariance checks in `checks/12b9259f7792/first-turn.json`.

## Remaining gate

Reviewer construction and qualification evidence are ready. Exact-source owner review, fresh native qualification/acceptance, and any training admission remain downstream and are not claimed here.
