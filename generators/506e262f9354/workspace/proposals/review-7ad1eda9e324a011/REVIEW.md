# Review — 506e262f9354 public-batch repair and parametric qualification
Task/source: `506e262f9354` v3.0.0; production generator SHA-256 remains `762a30ac71d7bb9e779a6ce0948247878740259cac499842ef991e2863f20ec5`.
Defect → repair: the prototype wrote public challenges while iterating private settings; it now plans and validates the full visible batch, rejects duplicate public IDs before any public write, and emits challenges in lexicographic ID order.
Promotion path: added a task-local adapter and finite `expansion_direction = up | down` contract while keeping `up` byte-exact to the canonical Racket program.
Focused verification: **79 passed in 5.81s**, plus clean Python compilation and a final scope/integrity check.
Writer replay: 2 episodes, 6 demonstrations, 8 queries, 7 distinct inputs, all 6 canonical pairs matched, zero surviving declared rivals, exact-byte public IDs, unique IDs, and sorted emission.
Protected qualification: both settings × seeds 0/17 produced 4 episodes, 28 label claims, and 40 protected-Racket evaluations with unique demo-only survivors.
Canonical authority is unchanged: normalized rule hash `d19e95f77d58`; exact canonical program SHA-256 `7d00cd1a50d3b572eb7a50d096cb5d01f0e7af4d8f9bc403d42a3b905b20dc6f`.
The variant remains `not_accepted`; `training_admitted=false`; no owner acceptance command was invoked.
Supplementary tickets: the blind NVARC prediction matched pair 4 exactly and the rule matched all 30 pairs; the pinned `grid_h` API honored 3 and rejected 2 as specified.
Remaining limit: qualification covers the declared finite setting space and two seeds, not every undeclared program or a measured training-gain claim.
Assessment: the selected repair and qualification work are complete and source-bound; maintainer action is limited to any later acceptance/training decision.

## What changed

- `workspace/parametric/prototype.py` is now version 1.1.0. Its writer computes all public payloads and identifiers before opening the public output phase. It verifies that each ID is the SHA-256 of the exact visible bytes, rejects duplicates before any public file exists, then writes the sorted batch.
- `generate_claims(...)` exposes deterministic Python-side episode claims without constructing a nested Racket bridge. The qualification worker independently replays every label through the protected Racket runtime.
- `workspace/parametric/adapter.py` and `promotion.json` define the bounded promotion interface: directions `up` and `down`, canonical default `up`, 3–8 demonstrations, and 1–8 queries.
- Focused tests cover the adapter contract, exact canonical default, settings/count validation, deterministic claims, protected qualification assumptions, sorted public emission, and duplicate-ID fail-closed behavior.
- The task README, evidence manifest, and `notes.md` now describe the repaired writer, bounded qualification evidence, and explicit non-acceptance boundary.

The exact changed-path inventory is retained in `checks/final/integrity.json`.

## Verification evidence

The public-writer regressions were first observed failing against the prior write-as-you-go behavior, then passing after the repair:

- Red: `checks/tdd-public-export-red/pytest.log`
- Green: `checks/tdd-public-export-green/pytest.log` — 11 passed

Fresh final receipts:

- `checks/final/selected-task-pytest.log` — 79 passed
- `checks/final/pycompile.log`
- `checks/final/writer-summary.json`
- `checks/final/506e262f9354-writer/report.json`
- `checks/final/qualification-summary.json`
- `checks/final/qualification-506e262f9354/qualification.json`
- `checks/final/integrity.json` — every scoped/hash/status assertion true

The production generator, canonical puzzle data, selected rule hash, and exact canonical Racket program remained unchanged. The final status is explicitly `not_accepted`, and no training admission is claimed.

## Supplementary tickets

### NVARC — ticket-4fe545dfc6c52086

Before reveal, pair 4 was predicted using this locked rule: “Double the canvas height, ignore auxiliary color-8 shapes, swap the colors at the ends of the horizontal 8-bar, place them at twice the original row, and copy each one to both lower diagonals.” The prediction matched exactly. A bounded skim then found the same explicit transformation matched all 30 retained pairs, with no bad pair indices. Verdict: `ok`.

Evidence: `checks/tickets/ticket-4fe545dfc6c52086/nvarc/`.

### API boundary — ticket-3b82645654e56bbf

One source-pinned valid/invalid comparison tested the advertised `AXES.grid_h` exact integer range. `grid_h=3` was honored and produced a height-3 grid with no self-check errors; `grid_h=2` failed closed with `ValueError: draw_int_diff('grid_h'): override 2 outside [3, 8]`. No peer source was edited and no safety finding was created.

Evidence: `checks/tickets/ticket-3b82645654e56bbf/result.json`.
