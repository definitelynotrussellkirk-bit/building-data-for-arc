# Review — dafb4f819b93

Task `dafb4f819b93` (`a406ac07` family); baseline generator SHA-256 `76a6435587f8b973716e6581f0f99cdec9e1e7c88c992aef3e8e51ffb6cb91c3`, final `4cb2197b77338fd386373618400ef0e81be47b5a9cbc9e58f1e4c463d83e4b1b`.
Defect → repair: fixed the retained test's hard-coded repository depth and private draw-state access; it is now packet-rooted and source-bound.
Defect → repair: added the missing executable semantic contract without changing generation behavior or the canonical Racket authority.
Built: separate **proposed/unapproved** `label_offset ∈ {0,1}` episode prototype; offset 0 is the exact canonical source and offset 1 is one guarded cyclic-label substitution.
Built: deterministic 3-demo/4-query materializer, public/private export, visible-byte IDs, exact Racket labeling, exhaustive manifest, canonical replay, and a source-regenerating verifier that rejects stale bindings and recomputed-manifest metadata tampering.
Authority: canonical rule hash `6bb5aaacd2ec` and canonical source SHA-256 `fd28f01b9690c2b68a529d5ecb88df555c53e93cc5254d1f6662017f1fdcf6cc` are unchanged.
Checks: packet-native audit passed 44 tests + 12 subtests and the strict semantic gate with required query rotations.
Prototype evidence: 2 settings, 2 episodes, 6 demonstrations, 8 queries, 4 canonical pairs, 0 declared rival ambiguities; standalone verification passed.
Adversarial evidence: 768 maximum-count inputs passed; forced retry recovered; over-limit counts and recomputed-manifest public/private tampering were rejected.
Supplementary tickets: the pinned `2920da6abe8a` authority crash reproduced without clearing its audit; a lawful `25e18d9bd322` witness refuted the centroid-distance shortcut with exact Racket agreement.
Status: complete for the assigned review; the parametric variant remains unapproved and is not admitted for training.
Remaining limit: finite evidence covers the two declared settings and retained seeds, not arbitrary alternative programs or population-level behavior.

## Changed source

- `repo/generators/dafb4f819b93/generator.py` — source-bound semantic declarations and lesson validation only.
- `repo/generators/dafb4f819b93/tests/test_generator_dafb4f819b93.py` — portable root/canonical loading and public axis access.
- `repo/generators/dafb4f819b93/tests/test_semantic_contract.py` — contract regression tests.
- `repo/generators/dafb4f819b93/tests/test_parametric_label_offset.py` — canonical parity, episode/export, verifier, and invalid-input tests.
- `repo/generators/dafb4f819b93/workspace/parametric/prototype.py` and `README.md` — proposed extension and runnable verifier.
- `repo/generators/dafb4f819b93/notes.md` — current decisions, evidence boundary, and approval status.

## Primary evidence

- `checks/dafb4f819b93-final-audit/result.json`
- `checks/parametric/dafb4f819b93-label-offset-v1/report.json`
- `checks/parametric/dafb4f819b93-adversarial.json`
- `checks/tickets/ticket-3adfc912a7344996/replay.json`
- `checks/tickets/ticket-4964d90872b2b95e/witness.json`
