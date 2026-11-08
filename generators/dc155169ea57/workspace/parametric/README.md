# Barrier-capacity prototype (not production-approved)

This task-local prototype materializes the selected Racket rule with
`barrier_capacity` 1, 2, or 3. Capacity 1 preserves the canonical program
bytes; capacities 2 and 3 change one checked threshold literal. Labels are
executed through Racket, and demonstrations must refute the finite declared
rival inventory before query sampling.

## Public/private export boundary

The exporter writes model-visible challenges only under:

`public/challenge-<sha256>.json`

The digest is SHA-256 of the exact canonical bytes returned by
`reviewer_support.public_challenge_bytes`: visible demonstration inputs and
outputs plus query inputs, with no setting, seed, program, query answer, or
ordinal. Public files are sorted by that digest, so changing request order or
private metadata cannot create a setting-associated public path.

Authoring evidence lives under `private/` and may contain parameters, programs,
reference query labels, rival fits, and the distinguishing witness. The root
manifest is also authoring evidence, not a model-visible challenge.

This prototype remains proposed. Finite rival checks are not a universal
identifiability proof and do not approve any variant for training.
