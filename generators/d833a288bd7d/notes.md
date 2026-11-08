# Working notes: d833a288bd7d

## 2026-10-24 review

- Reproduced teaching hole: seed 0, sample indices 10–12 produced three zero-turn demonstrations, while index 13 required an odd turn; a reverse-rotation rival therefore survived the lesson and disagreed on the query.
- Repair in version `3.0.1`: schedule the four quarter-turn classes across each four-example window, reject 180°-symmetric generated bitmaps for odd turns, preserve exact override semantics, and condition the canonical-profile prior on compatible turns while retaining its original overall rate.
- Added explicit reverse-rotation rival, witness, strict canonical-like predicate, and lesson-identifiability hooks. Portable tests cover canonical pairs, generation controls, profile diversity, the retained ambiguity, and the new teaching contract.
- Evidence: `WORK/checks/d833a288bd7d-tests/result.json` after final verification. No parametric variant was added.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 native parametric admission build

- Added a task-local native adapter with exact canonical default
  `source_cue=yellow_marker` and alternative `source_cue=minority_centroid`.
  Both settings share inputs; Step A derives an input-dependent source diagonal,
  and Step B consumes it with the L-cluster target diagonal to choose the final
  quarter-turn rotation.
- Supports deterministic prefix-stable 2–6 demonstrations and 1–4 queries. The
  fourth query is 30×30 with a dense 16×16 colored square. Public projections
  mask all query labels and are invariant to private settings, seed, program and
  query outputs.
- The first two demonstrations refute the other declared setting, reverse
  rotation, majority-centroid, four fixed-turn and four fixed-source rivals in a
  32-seed finite audit. No named rival survived; this is not a universal
  uniqueness claim.
- Native qualification passed for both settings at seeds 0 and 17 with three
  demonstrations, four queries and 40 protected-Racket evaluations. A protected
  wrong-intermediate witness replays successfully: on the selected
  `minority_centroid` query, substituting yellow source diagonal 2 for minority
  source diagonal 0 changes the rotation and final grid.
- Evidence: `workspace/parametric/evidence/manifest.json`,
  `WORK/checks/d833a288bd7d/qualification/qualification.json`, and
  `WORK/checks/d833a288bd7d/causal/witness.json`. Reviewer status is `ready`;
  owner exact-source acceptance and training admission remain pending.
