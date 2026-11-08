# Implementation handoff

- Canonical source: `reference.rkt` and byte-identical
  `workspace/parametric/canonical.rkt`.
- Native sampler/API: `workspace/parametric/adapter.py`.
- Base generator: `generator.py`; no advertised control axes.
- Contract: `workspace/parametric/promotion.json`.
- Reusable verification: `workspace/parametric/audit.py`.
- Sequential ablation: `workspace/parametric/wrong_order.rkt` and
  `workspace/parametric/causal-description.json`.

Run authoring preflight first, then run the audit against that exact preflight
receipt. These artifacts report reviewer-ready authoring evidence only; owner
registration, native qualification, acceptance, and training admission remain
separate gates.
