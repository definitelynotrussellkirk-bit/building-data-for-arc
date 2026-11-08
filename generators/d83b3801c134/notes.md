# Working notes: d83b3801c134

- **Decision:** keep the exact catalog rule as the `direction=one_to_two` default and add the nearby `direction=two_to_one` setting. The input markers supply a signed, scene-dependent vector; the second stage translates every green component by that vector.
- **Why this family:** the same input is valid under both directions, every pair distinguishes them, and the alternative preserves the source task's translation reasoning instead of adding a scalar or cosmetic parameter.
- **Sampler:** deterministic matched inputs, 2–6 demonstrations, 1–4 queries (qualification uses four), at least two green components, both directions in bounds, varied signed vectors, and a substantive 30x30 query.
- **Self-review:** the bounded 40-seed audit rejected opposite direction, first-component-only, two fixed vectors, copy-input, and fixed-origin rivals on all 80 setting episodes; no declared teaching hole or finite equivalence survived. See `workspace/parametric/evidence/current/audit.json`.
- **Native evidence:** authoring preflight and protected-Racket labels passed at `checks/d83b3801c134/qualification/`; the wrong-direction causal witness replayed at `checks/d83b3801c134/causal/witness.json`; sequential projection privacy passed at `checks/d83b3801c134/first-turn.json`.
- **Limit:** finite qualification/audit evidence does not prove universal uniqueness. Exact-source owner qualification and fresh acceptance replay remain the next integration step; no training admission is claimed.
