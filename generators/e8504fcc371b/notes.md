# Working notes: e8504fcc371b

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 full native build review

- **Base repair:** advanced the generator to `3.1.0`; replaced the coupled four-slot command/relation schedule with an eight-slot full Cartesian schedule. Every four-demo lesson now covers all commands and both placement relations and refutes the retained geometry/value hybrid. Tests now resolve the canonical source portably.
- **Canonical preservation:** `workspace/parametric/canonical.rkt` is byte-identical to rule `72176e994d8a` (`6541915b678759478881b5dcbc9b5ccde089bf86e03f055b73a6fc7d2bea5cf0`).
- **Parametric setting:** `trail_mode=border_hook` first traces the command-selected ray to obtain its endpoint and length, then consumes both values to continue clockwise around the perimeter for exactly that length. Inputs are matched across settings, deterministic and count-independent; 2–6 demonstrations and four queries are supported.
- **Domain/stress:** the input intentionally remains exactly one command plus one seed because the canonical rule selects the last command and last other nonzero cell. The 30×30 alternative output nevertheless changes 50 cells and spans at least 20 rows and columns in all bounded stress seeds.
- **Adversarial result:** the bounded probe passed 12 native jobs and 136 protected-Racket evaluations, refuting straight-only, fixed-hook-length and counterclockwise bypasses. A protected fixed-length-1 counterfactual changes the final hook.
- **Retained evidence:** `workspace/parametric/evidence/manifest.json` (SHA-256 `8784eced99f0ec44de7b1d89b245d0a36e31678fa646d3997c2bd47e2eccb36a`), `checks/e8504fcc371b/qualification/`, `checks/e8504fcc371b/causal/`, `checks/e8504fcc371b/first-turn.json`, and `checks/e8504fcc371b-tests/result.json`.
- **Status/limit:** authoring preflight and causal replay passed; this is ready for owner source review. It is not owner-accepted and admits no training data.
