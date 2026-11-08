# Working notes: a1ece4864521

- Repaired the base sampler to match the canonical anomaly grammar: 1–9
  anomalies, repeated colors, binary 0/8 corruptions, variable inferred 5x5
  lattices, strict override/type validation, and canonical self-checking.
- The exact selected canonical Racket bytes remain the default
  `fill_route=below_right`.  The alternative `phase_diagonal` reconstructs the
  latent lattice first, then routes each anomaly by its inferred clean phase.
- Adversarial review found that two demonstrations with the same row-major first
  anomaly phase left a first-phase-for-all shortcut alive.  The minimum lesson
  now crosses first phases 0 and 8 and refutes all ten declared rivals.
- Qualification support is deliberately bounded to 2–6 demonstrations and 1–4
  queries; native authoring evidence is not owner acceptance or training
  admission.
