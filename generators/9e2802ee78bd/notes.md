# Working notes: 9e2802ee78bd

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 reviewer repair and parametric build

- Repaired the generator's declared contract before extending it. Exact overrides are now observable and round-trip from pixels; unknown keys, booleans, inconsistent dimensions, damaged separators, and every declared degenerate fail closed. The canonical Racket rule remains byte-exact.
- Added native settings `post_transform=none` and `post_transform=flip_ud`. The alternate first computes the marker-selected canonical intermediate, then vertically flips that input-derived panel before pasting it into the destination region.
- A 12-job bounded protected-Racket audit retained four private queries per episode, checked matched inputs and prefix stability, exercised a 30x30 case, and rejected identity-source, flip-source, wrong post-transform, and alternate-setting rivals after 338 label evaluations.
- The wrong-intermediate causal witness substitutes the raw source panel for the marker-selected intermediate; protected replay changes 226 final cells.
- The canonical source row uses the supported legacy singleton-object form for `test`. `Catalog.challenge` normalizes it, but the private authoring preflight/witness/preview hash path iterates and hashes the raw form inconsistently. Task-local compatibility launchers normalize only that one row in memory, then delegate to the unmodified official tools; shared and canonical files are untouched.
- Source-bound task tests pass 5/5. The authoring preflight covers both settings at two fresh seeds with 4 demonstrations and 4 queries per job. This is reviewer evidence only: owner acceptance and training admission were not performed.
