# Working notes: a90d16507995

## Current decision

The canonical crop-and-stamp rule is sound and remains byte-for-byte unchanged: tightly crop the nonzero/non-9 source, clear the source, and paste the crop with the color-9 marker as its top-left anchor. The old generator constrained overrides through difficulty ranges and did not honestly realize several advertised blob/palette controls. Version 2.2.0 now strictly validates override names, enforces agreeing aliases, and realizes exact dimensions, blob size, palette size/distinct-color count, palette kind, and fixed controls.

## Native parametric family

- `stamp_only`: the exact 624-byte canonical Racket program.
- `stamp_majority_frame`: first perform the canonical crop-and-stamp, derive the unique majority nonzero color from the stamped crop, then draw a one-cell exterior frame around the destination crop in that color.

The second setting is a genuine input-dependent `A -> stamped crop and color counts -> B` rule. The protected witness substitutes the source crop's non-majority top-left color as a wrong intermediate and changes the final output. The family supports 2–6 demonstrations and 1–4 query prefixes while retaining four distinct private queries. Query 4 is a lawful 30×30 case with a connected 12×12 irregular source containing at least 80 cells.

## Repairs made during self-review

Two construction bugs were found and fixed before qualification. Interior notches could disconnect a row suffix, so irregular masks now notch only from the right edge and are connectivity-checked. Fixed-size canvases could not always fit both the source and a framed destination for the largest crops, so canvas dimensions are derived constructively from crop dimensions. The teaching bank refutes copy-not-move, center/bottom-right anchor, no-frame, top-left-color, least-frequency-color, and source-location frame shortcuts.

## Retained evidence

- Focused task tests: `checks/a90d16507995-task-tests/result.json` — 23/23 passed.
- Bounded adversarial audit: `checks/a90d16507995/self-audit.json` — 384 cases, 2,944 labeled pairs, 1,344 rival checks, 64 causal checks, zero failures.
- Base-control audit: `checks/base-control-audit.json` — 128 exact-control scenarios, zero failures for this target.
- Protected authoring preflight: `checks/a90d16507995/qualification/qualification.json` and sibling `execution.json` — both settings, seeds 0 and 17, 32 protected Racket evaluations.
- Source-bound causal witness: `checks/a90d16507995/causal/witness.json`; protected replay: `checks/a90d16507995/causal/replay.json`.
- Sequential public projection: 16 verified single-query views and 24 first-turn invariance checks in `checks/a90d16507995/first-turn.json`.

## Tooling finding and remaining gate

The canonical record stores its single `test` pair as a dictionary, while the shared authoring preflight assumes every split is a list. A narrowly tested normalization patch is retained at `checks/tooling/review_base_preflight-single-pair.patch`; shared source was restored unchanged to honor assignment scope. Reviewer construction and qualification evidence are ready. Exact-source owner review, fresh native qualification/acceptance, and any training admission remain downstream and are not claimed here.
