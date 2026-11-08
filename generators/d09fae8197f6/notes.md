# Working notes: d09fae8197f6

## 2026-10-23 — task-local `orientation_scope` prototype

Decision: keep the production generator and canonical authority unchanged, and prototype one episode-level parameter under `workspace/parametric/`:

- `dihedral` is the default and uses the exact canonical eight-orientation Racket text.
- `rotations` is the proposed alternative and changes only the orientation list to `t0..t3`.
- The setting is selected once per episode. Demonstration and query counts are independent; retained evidence uses 3 demonstrations and 4 distinct queries.
- Sampling reuses lawful production inputs but rejects duplicates, identity behavior, or pairs where the two settings agree. Both settings must visibly stamp every retained pair.
- Public challenge IDs are SHA-256 identities of exact visible challenge bytes only. Hidden setting, seed, source metadata, program text, and query answers stay private.

Source identities stayed fixed: generator SHA-256 `7ede233024db1986cad07ad92f207b8a93a7e74714d2e1c9d9eb2a4ce03a4937`, `RULE_HASH` `be26cdb395f0`, canonical program SHA-256 `2c66b6d50abfdfa3b7a96e932162ec3e66bbdca8dcbfd3863e75a1b81fe057f8`.

Evidence:

- `checks/parametric/focused-tests.json`: 25 focused tests passed.
- `checks/parametric/orientation-scope-v1/summary.json`: live protected Racket executed 14 selected labels and 14 rival labels; every demonstration refuted the other setting and every query distinguished it.
- `checks/parametric/orientation-scope-adversarial-v1.json`: 40 ordinary episodes plus one maximum-count episode, 292 pairs, zero sampler failures; public/private projection checks passed.
- `checks/parametric/source-integrity.json`: canonical generator, rule hash, program hash, and exact default program all remained unchanged.

Limit: this is a proposed task-local authoring prototype, not production approval or training admission. The sampler probe is bounded, not an all-seed proof.

Next useful action: an independent maintainer can decide whether `orientation_scope` is pedagogically valuable enough to promote into a first-class generator API; promotion should preserve the exact `dihedral` default and rerun the retained Racket evidence.
