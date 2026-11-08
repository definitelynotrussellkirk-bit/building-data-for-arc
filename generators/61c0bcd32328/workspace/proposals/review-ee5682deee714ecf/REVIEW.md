# Review: 61c0bcd32328

Task `61c0bcd32328` / ARC family `bc93ec48`; generator advanced from `2.0.0` to `2.1.0` (SHA-256 `4f45d334880485ba8e7926f352f6f9c919dad53df3a9b868af43703964dff4ec`).
Defect → repair: corner anchors excluded the one-cell shape, so lessons never taught that singleton corner components are copied; corner anchors now sample all declared shapes.
Canonical rule: unchanged. Exact canonical Racket SHA-256 `0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e`; normalized authority hash `e3835c9a174e`.
Proposed prototype: episode-fixed `direction={clockwise,counterclockwise}`, with `clockwise` byte-identical to the canonical program and only the corner translation table changed for the alternative.
Prototype evidence: `checks/parametric/61c0bcd32328-direction-v1/report.json`; 2 episodes, 3 demos + 4 distinct queries each, both settings, 66 Racket evaluations/replays, zero surviving direction rivals.
Teaching evidence: every episode’s demonstrations refute the opposite direction and the first demonstration contains a singleton corner component, refuting the retained “ignore singleton noise” shortcut.
Portable selected-task gate: `checks/final/task-tests/` — 22/22 tests passed under the packet Racket runtime.
Adversarial surfaces: sampler/count boundary and parameter/Racket plus public/private projection; retained checks reject duplicate visible payloads, verify exact visible-byte IDs, and fail requests beyond ten fixed profile slots.
Remaining limit: evidence is bounded to seeds 0 and 1 and the declared ten-profile schedule; it is not an all-input proof or production approval.
Disposition: routine canonical generator repair plus a useful proposed extension; maintainer attention is needed only for any future production parametric API/admission decision.

## Concrete changes

- `generator.py`: include singleton shapes in corner-anchor sampling and bump `VERSION` to `2.1.0`.
- `tests/test_generator_61c0bcd32328.py`: add singleton sampling/reference regressions, use portable task loading, and normalize formatting-only Racket differences in source-sync assertions.
- `workspace/parametric/prototype.py`: source-bound Racket materialization, deterministic episode construction, rival checks, public/private projection, exact hash receipts, replay, and a CLI evidence writer.
- `tests/test_parametric_direction.py`: exact-default, guarded alternative, real-Racket behavior, episode identifiability, public-ID invariance, evidence hashes, and boundary tests.

## Verification scope

The full production battery was not run because the canonical law and shared runtime were unchanged. The selected-task portable suite and the prototype’s Racket-backed evidence directly exercise the changed generator lesson and all new prototype surfaces. No canonical data, frozen fixture, approval record, or shared runtime file was edited.

## Supplementary tickets

- `ticket-26b64f8e03519161` (`audit_replay`): **finding**. The exact retained `260f488cb5a8` override-coercion audit reproduced byte-for-byte; three non-literal integer overrides were accepted and all generated grids passed `self_check`. The peer source was not changed; see `AUDIT.md` and `checks/tickets/ticket-26b64f8e03519161/receipt.json`.
- `ticket-b9b6caf3ff828e0e` (`adversarial_witness`): **completed**. A lawful hard-band `3108da8bf9e8` input refuted the plausible “sort within original macro-rows, then rank whole rows by total count” shortcut. Canonical Racket matched the Python mirror and differed from the shortcut in 28 cells; see `checks/tickets/ticket-b9b6caf3ff828e0e/witness.json`.
