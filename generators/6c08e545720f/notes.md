# Working notes: 6c08e545720f

## Current decision

Keep the base generator and exact canonical default unchanged. The native family adds:

- `connect_only`: exact canonical same-color diagonal connection.
- `connect_then_mark_crossings`: connect all paired endpoints first, detect genuine two-color X crossings in that completed intermediate, then recolor each crossing center with the input's singleton cue color.

Inputs are matched across settings and support 2–6 demonstrations plus four distinct queries. Asymmetric endpoint distances make pair-midpoint marking wrong; cue colors vary across the minimum two demonstrations; sparse inputs contain no pre-existing X; and the 30×30 query has two independent crossings with at least 45 non-background output cells.

## Repaired review finding

The first protected preflight rejected the canonical default even though 14 Python tests and the bounded audit were green. Root cause: the Python mirror resolved crossing-center overwrites in row-major first-occurrence color order, while the protected canonical DSL traverses these monochrome singleton objects in numeric color order. On seed 0, demonstration 1, Python predicted color 2 at `(5,5)` while protected Racket produced 3. A RED/GREEN regression now pins numeric color order; the refreshed 15-test suite, manifest, audit, and protected preflight pass.

## Evidence and limits

- Self-review: `workspace/parametric/evidence/current/self-review.json` — 192 setting-paired episodes, 2,944 labeled pairs, 192 exact 30×30 queries, zero survivors for `connect_only`, `fixed_zero`, `pair_midpoints`, and `input_crossings`.
- Inventory: `workspace/parametric/evidence/manifest.json`.
- Authoring preflight: `checks/6c08e545720f/qualification/qualification.json` with 32 protected-Racket evaluations.
- Causal replay: `checks/6c08e545720f/causal/witness.json`.
- Public projection/privacy: `checks/6c08e545720f/preview-verify.json` and `checks/6c08e545720f/first-turn.json`.

This remains reviewer-ready authoring evidence only. Exact-source owner review, native qualification/acceptance, and any training admission are pending.
